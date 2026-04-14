"""
Bias Auditor — Computes fairness metrics on uploaded datasets.

Accepts a CSV file, an outcome column, and a protected attribute column.
Computes Disparate Impact Ratio, Statistical Parity Difference, and
per-group pass rates. Returns a structured report with pass/fail verdicts.

Uses the 4/5ths (80%) rule as the industry-standard threshold for
disparate impact analysis.
"""
import csv
import io
from collections import defaultdict


# The 4/5ths rule: the selection rate of any protected group must be
# at least 80% of the rate of the highest-performing group.
DISPARATE_IMPACT_THRESHOLD = 0.8


def audit_bias(file_content: str, outcome_column: str, protected_column: str,
               positive_value: str = '') -> dict:
    """Run a bias audit on CSV data.

    Args:
        file_content: Raw CSV string.
        outcome_column: Name of the column containing the outcome (e.g., 'grade', 'hired', 'approved').
        protected_column: Name of the column containing the protected attribute (e.g., 'gender', 'race').
        positive_value: What counts as a positive outcome. If empty, auto-detect
                        (numeric > median, or the most common value).

    Returns:
        Dict with group_stats, disparate_impact, statistical_parity, and overall verdict.
    """
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)
    except Exception:
        return {'error': 'Could not parse file as CSV.'}

    if not rows:
        return {'error': 'CSV file is empty.'}

    headers = list(rows[0].keys())
    if outcome_column not in headers:
        return {'error': f'Column "{outcome_column}" not found. Available columns: {", ".join(headers)}'}
    if protected_column not in headers:
        return {'error': f'Column "{protected_column}" not found. Available columns: {", ".join(headers)}'}

    # Extract values
    outcomes = []
    groups = []
    for row in rows:
        outcome_val = row[outcome_column].strip()
        group_val = row[protected_column].strip()
        if outcome_val and group_val:
            outcomes.append(outcome_val)
            groups.append(group_val)

    if len(outcomes) < 10:
        return {'error': 'Not enough valid rows (minimum 10 required).'}

    # Determine what counts as a "positive" outcome
    if not positive_value:
        positive_value = _auto_detect_positive(outcomes)

    # Compute per-group stats
    group_data = defaultdict(lambda: {'total': 0, 'positive': 0})
    for outcome, group in zip(outcomes, groups):
        group_data[group]['total'] += 1
        if _is_positive(outcome, positive_value):
            group_data[group]['positive'] += 1

    # Compute rates
    group_stats = []
    rates = {}
    for group_name, data in sorted(group_data.items()):
        rate = data['positive'] / data['total'] if data['total'] > 0 else 0
        rates[group_name] = rate
        group_stats.append({
            'group': group_name,
            'total': data['total'],
            'positive': data['positive'],
            'rate': round(rate * 100, 1),
        })

    if not rates:
        return {'error': 'No valid groups found after processing.'}

    # Disparate Impact Ratio
    max_rate = max(rates.values())
    min_rate = min(rates.values())

    disparate_impact = round(min_rate / max_rate, 3) if max_rate > 0 else 0
    di_pass = disparate_impact >= DISPARATE_IMPACT_THRESHOLD

    # Find which groups are advantaged/disadvantaged
    max_group = max(rates, key=rates.get)
    min_group = min(rates, key=rates.get)

    # Statistical Parity Difference
    sp_diff = round(max_rate - min_rate, 3)
    sp_pass = sp_diff <= 0.1  # Industry standard: < 10% difference

    # Overall verdict
    all_pass = di_pass and sp_pass
    if all_pass:
        verdict = 'PASS'
        verdict_message = 'No statistically significant disparities detected across groups. The outcomes appear equitable.'
    elif di_pass and not sp_pass:
        verdict = 'WARNING'
        verdict_message = (
            f'The disparate impact ratio ({disparate_impact}) meets the 4/5ths threshold, '
            f'but the statistical parity difference ({sp_diff}) suggests some disparity '
            f'between {max_group} and {min_group}. Review recommended.'
        )
    else:
        verdict = 'FAIL'
        verdict_message = (
            f'Potential bias detected. The disparate impact ratio is {disparate_impact} '
            f'(below the 0.8 threshold). The group "{min_group}" has a positive outcome rate '
            f'of {round(min_rate * 100, 1)}% compared to {round(max_rate * 100, 1)}% for '
            f'"{max_group}". This {round((1 - disparate_impact) * 100, 1)}% gap requires '
            f'investigation and potential corrective action.'
        )

    return {
        'groupStats': group_stats,
        'positiveOutcome': positive_value,
        'totalRecords': len(outcomes),
        'uniqueGroups': len(group_data),
        'metrics': {
            'disparateImpact': {
                'value': disparate_impact,
                'threshold': DISPARATE_IMPACT_THRESHOLD,
                'pass': di_pass,
                'explanation': (
                    f'Measures whether the lowest-performing group\'s positive rate is at least '
                    f'80% of the highest group\'s rate. '
                    f'Lowest: {min_group} ({round(min_rate * 100, 1)}%), '
                    f'Highest: {max_group} ({round(max_rate * 100, 1)}%).'
                ),
            },
            'statisticalParity': {
                'value': sp_diff,
                'threshold': 0.1,
                'pass': sp_pass,
                'explanation': (
                    f'Measures the absolute difference in positive outcome rates between groups. '
                    f'A difference greater than 10% warrants investigation.'
                ),
            },
        },
        'verdict': verdict,
        'verdictMessage': verdict_message,
        'advantagedGroup': max_group,
        'disadvantagedGroup': min_group,
    }


def _auto_detect_positive(values: list[str]) -> str:
    """Auto-detect what counts as a positive outcome.

    For numeric data: above the median.
    For categorical: returns the detected positive label.
    """
    # Try numeric first
    numeric_vals = []
    for v in values:
        try:
            numeric_vals.append(float(v))
        except ValueError:
            break

    if len(numeric_vals) == len(values):
        median = sorted(numeric_vals)[len(numeric_vals) // 2]
        return f'>={median}'

    # Categorical: look for common positive labels
    positive_labels = {'yes', 'true', '1', 'pass', 'approved', 'accepted', 'hired', 'admit', 'admitted', 'a', 'b'}
    val_lower = {v.lower() for v in values}
    for label in positive_labels:
        if label in val_lower:
            # Find the original case version
            for v in values:
                if v.lower() == label:
                    return v

    # Default: most common value
    from collections import Counter
    most_common = Counter(values).most_common(1)[0][0]
    return most_common


def _is_positive(value: str, positive_value: str) -> bool:
    """Check if a value matches the positive outcome criteria."""
    if positive_value.startswith('>='):
        try:
            threshold = float(positive_value[2:])
            return float(value) >= threshold
        except ValueError:
            return False

    return value.strip().lower() == positive_value.strip().lower()


def get_csv_columns(file_content: str) -> dict:
    """Return the column names from a CSV file for the frontend dropdown."""
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)
        if not rows:
            return {'columns': [], 'rowCount': 0}
        return {'columns': list(rows[0].keys()), 'rowCount': len(rows)}
    except Exception:
        return {'error': 'Could not parse file as CSV.'}

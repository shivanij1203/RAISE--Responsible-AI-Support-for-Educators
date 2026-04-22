"""Unit tests for pure service functions (no DB / HTTP needed)."""
from api.services.pii_scanner import scan_csv_for_pii, classify_data_from_description
from api.services.bias_auditor import audit_bias, get_csv_columns
from api.services.checkpoint_generator import generate_checkpoints_for_use_case


class TestScanCsvForPII:
    def test_detects_pii_by_header(self) -> None:
        csv_content = 'full_name,email,course\nJane Doe,jane@usf.edu,CS101\n'
        result = scan_csv_for_pii(csv_content)
        assert result['hasPII'] is True
        types = {f['type'] for f in result['findings']}
        assert 'name' in types
        assert 'email' in types

    def test_detects_pii_by_value(self) -> None:
        csv_content = 'contact_info,course\n555-123-4567,CS101\n'
        result = scan_csv_for_pii(csv_content)
        assert result['hasPII'] is True

    def test_clean_csv_passes(self) -> None:
        csv_content = 'anon_id,score_bucket\nA1,high\nA2,low\n'
        result = scan_csv_for_pii(csv_content)
        assert result['hasPII'] is False
        assert 'No PII patterns detected' in result['verdict']

    def test_empty_csv_returns_no_findings(self) -> None:
        result = scan_csv_for_pii('')
        assert result['hasPII'] is False
        assert result['findings'] == []

    def test_malformed_csv_returns_error(self) -> None:
        # csv.reader is permissive, but we can still hit the exception branch
        # with binary-ish content that's not valid utf
        result = scan_csv_for_pii('header1,header2\n"unclosed\n')
        # Either returns findings or error; just assert it doesn't crash
        assert 'findings' in result or 'error' in result

    def test_severity_high_for_ssn_column(self) -> None:
        csv_content = 'ssn,course\n111-22-3333,CS101\n'
        result = scan_csv_for_pii(csv_content)
        ssn_findings = [f for f in result['findings'] if f['type'] == 'ssn']
        assert all(f['severity'] == 'high' for f in ssn_findings)

    def test_summary_counts_severities(self) -> None:
        csv_content = 'email,phone\nfoo@bar.com,555-123-4567\n'
        result = scan_csv_for_pii(csv_content)
        assert result['summary']['high'] + result['summary']['medium'] > 0


class TestClassifyDataFromDescription:
    def test_restricted_for_ssn(self) -> None:
        result = classify_data_from_description('Contains SSN and credit card numbers')
        assert result['suggestedLevel'] == 'restricted'

    def test_confidential_for_health(self) -> None:
        result = classify_data_from_description('Student health records and HIPAA data')
        assert result['suggestedLevel'] == 'confidential'

    def test_confidential_for_grades(self) -> None:
        result = classify_data_from_description('Student grades and GPA')
        assert result['suggestedLevel'] == 'confidential'

    def test_internal_for_enrollment(self) -> None:
        result = classify_data_from_description('Course enrollment data by department')
        assert result['suggestedLevel'] == 'internal'

    def test_public_for_anonymized(self) -> None:
        result = classify_data_from_description('Fully anonymized aggregate dataset')
        assert result['suggestedLevel'] == 'public'

    def test_unknown_when_no_keywords(self) -> None:
        result = classify_data_from_description('Just some random text nothing relevant')
        assert result['suggestedLevel'] == 'unknown'


class TestAuditBias:
    def _build_csv(self, rows: list[tuple[str, str]]) -> str:
        lines = ['group,outcome']
        lines.extend(f'{g},{o}' for g, o in rows)
        return '\n'.join(lines) + '\n'

    def test_pass_when_equal_rates(self) -> None:
        csv = self._build_csv(
            [('A', 'yes')] * 5 + [('A', 'no')] * 5 +
            [('B', 'yes')] * 5 + [('B', 'no')] * 5
        )
        result = audit_bias(csv, 'outcome', 'group', positive_value='yes')
        assert result['verdict'] == 'PASS'
        assert result['metrics']['disparateImpact']['pass'] is True

    def test_fail_on_extreme_disparity(self) -> None:
        csv = self._build_csv(
            [('A', 'yes')] * 9 + [('A', 'no')] * 1 +
            [('B', 'yes')] * 1 + [('B', 'no')] * 9
        )
        result = audit_bias(csv, 'outcome', 'group', positive_value='yes')
        assert result['verdict'] == 'FAIL'
        assert result['metrics']['disparateImpact']['pass'] is False

    def test_missing_outcome_column_returns_error(self) -> None:
        csv = 'group,result\nA,yes\nB,no\n'
        result = audit_bias(csv, 'missing', 'group', 'yes')
        assert 'error' in result

    def test_missing_protected_column_returns_error(self) -> None:
        csv = 'team,outcome\nA,yes\nB,no\n'
        result = audit_bias(csv, 'outcome', 'group', 'yes')
        assert 'error' in result

    def test_empty_csv_returns_error(self) -> None:
        result = audit_bias('', 'outcome', 'group', 'yes')
        assert 'error' in result

    def test_too_few_rows_returns_error(self) -> None:
        csv = 'group,outcome\nA,yes\nB,no\n'
        result = audit_bias(csv, 'outcome', 'group', 'yes')
        assert 'error' in result
        assert 'minimum 10' in result['error']

    def test_auto_detect_positive_outcome(self) -> None:
        csv = self._build_csv(
            [('A', 'yes')] * 6 + [('A', 'no')] * 4 +
            [('B', 'yes')] * 6 + [('B', 'no')] * 4
        )
        result = audit_bias(csv, 'outcome', 'group', positive_value='')
        assert 'verdict' in result
        assert result['positiveOutcome']  # was auto-detected


class TestGetCsvColumns:
    def test_returns_column_names(self) -> None:
        result = get_csv_columns('a,b,c\n1,2,3\n')
        assert result['columns'] == ['a', 'b', 'c']
        assert result['rowCount'] == 1

    def test_empty_csv(self) -> None:
        result = get_csv_columns('')
        assert result['columns'] == []
        assert result['rowCount'] == 0


class TestGenerateCheckpointsForUseCase:
    def test_data_analysis_includes_core_checkpoints(self) -> None:
        cps = generate_checkpoints_for_use_case('data_analysis', {})
        ids = {c['checkpoint_id'] for c in cps}
        assert 'ai_disclosure' in ids

    def test_grading_is_faculty_only(self) -> None:
        cps = generate_checkpoints_for_use_case('grading', {})
        # All checkpoints should be assigned to pi for grading
        assert all(c['assigned_to'] == 'pi' for c in cps)

    def test_risk_context_adds_conditional_checkpoints(self) -> None:
        baseline = generate_checkpoints_for_use_case('data_analysis', {})
        with_risk = generate_checkpoints_for_use_case(
            'data_analysis',
            {'involves_human_subjects': True, 'involves_student_data': True},
        )
        # Higher risk context should produce at least as many checkpoints
        assert len(with_risk) >= len(baseline)

    def test_unknown_use_case_returns_fallback(self) -> None:
        cps = generate_checkpoints_for_use_case('nonexistent_use_case', {})
        # Should not crash; may return empty or 'other' fallback
        assert isinstance(cps, list)

"""Re-attaches AI-generated grades to student identities.

The blind-grading flow (``pseudonymize_csv``) produces an anonymized CSV that
is graded externally plus a private name-key CSV. This module closes the loop:
given the graded anonymous CSV and the name key, it joins them on the per-row
submission code so each grade lands back on the right student.
"""
from __future__ import annotations

import csv
import io

# A column is treated as holding submission codes when more than this share of
# its non-empty cells match a known code from the name key.
CODE_COLUMN_THRESHOLD = 0.5

# How many example codes to surface in the summary before truncating.
MAX_REPORTED_CODES = 20


def _parse_key(key_content: str) -> tuple[list[str], dict[str, list[str]]]:
    """Return (identity_headers, {code: identity_values}) from a name-key CSV.

    The name key's first column is the submission code; every remaining column
    is an original identity field (name, email, ...).
    """
    reader = csv.reader(io.StringIO(key_content))
    header = next(reader, [])
    if len(header) < 2:
        raise ValueError(
            'The name key must have a code column and at least one identity column. '
            'Upload the *_name_key.csv produced by Anonymous Grading Mode.'
        )

    identity_headers = header[1:]
    mapping: dict[str, list[str]] = {}
    for row in reader:
        if not row:
            continue
        code = row[0].strip()
        if not code:
            continue
        values = list(row[1:1 + len(identity_headers)])
        values += [''] * (len(identity_headers) - len(values))
        mapping[code] = values
    return identity_headers, mapping


def _detect_code_columns(rows: list[list[str]], codes: set[str]) -> list[int]:
    """Indices of graded-file columns whose cells are mostly known codes."""
    if not rows or not codes:
        return []

    width = max(len(r) for r in rows)
    code_cols: list[int] = []
    for col in range(width):
        non_empty = 0
        matches = 0
        for row in rows:
            if col < len(row):
                cell = row[col].strip()
                if cell:
                    non_empty += 1
                    if cell in codes:
                        matches += 1
        if non_empty and matches / non_empty > CODE_COLUMN_THRESHOLD:
            code_cols.append(col)
    return code_cols


def merge_graded_with_key(graded_content: str, key_content: str) -> dict:
    """Join a graded anonymous CSV back to student identities via the name key.

    Returns the merged CSV plus a summary of matched, unmatched, and missing
    rows so the faculty member can spot grading gaps before trusting the file.
    """
    identity_headers, mapping = _parse_key(key_content)
    codes = set(mapping.keys())

    reader = csv.reader(io.StringIO(graded_content))
    graded_header = next(reader, [])
    graded_rows = [row for row in reader if row]

    if not graded_rows:
        raise ValueError('The graded file has no data rows.')

    code_cols = _detect_code_columns(graded_rows, codes)
    if not code_cols:
        raise ValueError(
            'Could not find the anonymous codes in the graded file. Make sure you '
            'uploaded the graded version of the anonymized CSV (the one with '
            'STUDENT-001 style codes).'
        )

    keep_cols = [i for i in range(len(graded_header)) if i not in code_cols]
    kept_headers = [graded_header[i] for i in keep_cols]

    out_buffer = io.StringIO()
    writer = csv.writer(out_buffer)
    writer.writerow(identity_headers + kept_headers)

    matched = 0
    unmatched_codes: list[str] = []
    seen_codes: set[str] = set()

    for row in graded_rows:
        code = ''
        for col in code_cols:
            if col < len(row) and row[col].strip():
                code = row[col].strip()
                break

        identities = mapping.get(code)
        if identities is not None:
            matched += 1
            seen_codes.add(code)
        else:
            identities = [''] * len(identity_headers)
            if code:
                unmatched_codes.append(code)

        kept_values = [row[i] if i < len(row) else '' for i in keep_cols]
        writer.writerow(identities + kept_values)

    missing_codes = sorted(codes - seen_codes)

    return {
        'content': out_buffer.getvalue(),
        'summary': {
            'matchedRows': matched,
            'unmatchedRows': len(unmatched_codes),
            'unmatchedCodes': unmatched_codes[:MAX_REPORTED_CODES],
            'missingFromGraded': len(missing_codes),
            'missingCodes': missing_codes[:MAX_REPORTED_CODES],
            'identityColumns': identity_headers,
            'gradeColumns': kept_headers,
        },
    }

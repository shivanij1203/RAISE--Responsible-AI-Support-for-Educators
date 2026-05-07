"""PII Redactor.

Takes a CSV plus the findings from the PII scanner and returns a cleaned
copy with identity-revealing fields masked. Non-identifying fields like
grades and enrollment, which the scanner flags for FERPA review but are
typically the research data itself, are left untouched.
"""

from __future__ import annotations

import csv
import io
import re

from .pii_scanner import scan_csv_for_pii

REDACTION_TOKEN = '[REDACTED]'

IDENTITY_REVEALING_TYPES = {
    'name',
    'email',
    'phone',
    'ssn',
    'address',
    'dob',
    'date_of_birth',
    'id_number',
    'ip_address',
}

CELL_REDACTORS = {
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'phone': re.compile(r'(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'date_of_birth': re.compile(r'\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(19|20)\d{2}\b'),
    'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
}


def _columns_to_redact(findings: list[dict]) -> dict[int, str]:
    """Map column_index -> pii_type for columns flagged as identity-revealing."""
    result: dict[int, str] = {}
    for f in findings:
        ptype = f.get('type')
        idx = f.get('column_index')
        if ptype in IDENTITY_REVEALING_TYPES and isinstance(idx, int):
            result[idx] = ptype
    return result


def _scrub_cell_values(cell: str) -> str:
    """Apply value-pattern redaction to a single cell.

    Used for cells outside flagged columns where stray PII may still appear
    (e.g., a 'notes' column with an embedded email).
    """
    cleaned = cell
    for pattern in CELL_REDACTORS.values():
        cleaned = pattern.sub(REDACTION_TOKEN, cleaned)
    return cleaned


def pseudonymize_csv(file_content: str, code_prefix: str = 'STUDENT') -> dict:
    """Replace identity columns with stable per-row codes, return two CSVs.

    The 'anonymous' CSV is what the faculty pastes into the AI grading tool:
    each row's identity columns are replaced with a stable code like STUDENT-001.
    The 'name key' CSV is private to the faculty: it maps each code back to
    the original identity values so grades can be re-attached after AI grading.
    """
    scan = scan_csv_for_pii(file_content)
    findings = scan.get('findings', [])
    redact_columns = _columns_to_redact(findings)

    reader = csv.reader(io.StringIO(file_content))
    headers = next(reader, [])

    if not redact_columns:
        empty_buf = io.StringIO()
        writer = csv.writer(empty_buf)
        writer.writerow(headers)
        for row in reader:
            writer.writerow(row)
        return {
            'anonymizedContent': empty_buf.getvalue(),
            'mappingContent': '',
            'summary': {
                'columnsAnonymized': [],
                'rowsCoded': 0,
                'identityFieldsFound': False,
                'codePrefix': code_prefix,
            },
        }

    anon_buffer = io.StringIO()
    anon_writer = csv.writer(anon_buffer)
    anon_writer.writerow(headers)

    sorted_indices = sorted(redact_columns.keys())
    map_header_names = [headers[i] if i < len(headers) else f'Column {i + 1}' for i in sorted_indices]
    map_buffer = io.StringIO()
    map_writer = csv.writer(map_buffer)
    map_writer.writerow(['submission_id'] + map_header_names)

    rows_coded = 0
    for row_index, row in enumerate(reader, start=1):
        code = f'{code_prefix}-{row_index:03d}'
        new_row = list(row)
        identity_values: list[str] = []
        for i in sorted_indices:
            if i < len(new_row):
                identity_values.append(new_row[i])
                new_row[i] = code
            else:
                identity_values.append('')
        # Scrub any stray inline PII in non-identity cells too
        for i in range(len(new_row)):
            if i not in redact_columns:
                new_row[i] = _scrub_cell_values(new_row[i])
        anon_writer.writerow(new_row)
        map_writer.writerow([code] + identity_values)
        rows_coded += 1

    columns_anonymized = [
        {
            'columnIndex': i,
            'columnName': headers[i] if i < len(headers) else f'Column {i + 1}',
            'piiType': redact_columns[i],
        }
        for i in sorted_indices
    ]

    return {
        'anonymizedContent': anon_buffer.getvalue(),
        'mappingContent': map_buffer.getvalue(),
        'summary': {
            'columnsAnonymized': columns_anonymized,
            'rowsCoded': rows_coded,
            'identityFieldsFound': True,
            'codePrefix': code_prefix,
            'codeRange': f'{code_prefix}-001 through {code_prefix}-{rows_coded:03d}' if rows_coded else '',
        },
    }


def redact_csv(file_content: str) -> dict:
    """Return a redacted version of the CSV plus a summary of what changed.

    Steps:
    1. Run the PII scanner to identify identity-revealing columns.
    2. Replace every non-empty cell in those columns with [REDACTED].
    3. For other columns, scrub stray inline PII (emails, phones, SSNs).
    Non-identifying fields like grades and enrollment are left intact.
    """
    scan = scan_csv_for_pii(file_content)
    findings = scan.get('findings', [])
    redact_columns = _columns_to_redact(findings)

    reader = csv.reader(io.StringIO(file_content))
    headers = next(reader, [])
    out_buffer = io.StringIO()
    writer = csv.writer(out_buffer)
    writer.writerow(headers)

    rows_redacted = 0
    cells_redacted = 0
    cells_inline_scrubbed = 0

    for row in reader:
        new_row = list(row)
        row_changed = False
        for i, cell in enumerate(new_row):
            if i in redact_columns:
                if cell.strip():
                    new_row[i] = REDACTION_TOKEN
                    cells_redacted += 1
                    row_changed = True
            else:
                scrubbed = _scrub_cell_values(cell)
                if scrubbed != cell:
                    new_row[i] = scrubbed
                    cells_inline_scrubbed += 1
                    row_changed = True
        if row_changed:
            rows_redacted += 1
        writer.writerow(new_row)

    redacted_columns = [
        {'columnIndex': idx, 'columnName': headers[idx] if idx < len(headers) else f'Column {idx + 1}', 'piiType': ptype}
        for idx, ptype in sorted(redact_columns.items())
    ]

    return {
        'content': out_buffer.getvalue(),
        'summary': {
            'columnsRedacted': redacted_columns,
            'rowsAffected': rows_redacted,
            'cellsRedactedByColumn': cells_redacted,
            'cellsScrubbedInline': cells_inline_scrubbed,
            'identityFieldsFound': len(redact_columns) > 0,
        },
    }

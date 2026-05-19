"""Automated checkpoint verification endpoints.

Provides file-based scanning for PII detection, FERPA compliance checks,
and keyword-based data classification suggestions.
"""
import base64
import re
import zipfile

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.models import Project, Checkpoint
from api.services import notification_service
from api.services import audit_service
from api.services.pii_scanner import scan_csv_for_pii, classify_data_from_description
from api.services.pii_redactor import redact_csv, pseudonymize_csv
from api.services.grade_merger import merge_graded_with_key
from api.services.document_anonymizer import anonymize_submissions, read_archive
from api.services.pdf_text_extractor import extract_text_from_pdf
from api.services.bias_auditor import audit_bias, get_csv_columns

# Limits for the document anonymizer batch endpoint.
MAX_TOTAL_DOC_UPLOAD = 50 * 1024 * 1024
MAX_DOC_COUNT = 300


def _maybe_notify_verification(
    request,
    scan_type: str,
    verdict: str,
) -> None:
    """If the request includes project_id + checkpoint_id, fire a notification
    and append a verification event to the activity audit log."""
    project_id = request.data.get('project_id')
    checkpoint_id = request.data.get('checkpoint_id')
    if not project_id or not checkpoint_id:
        return
    try:
        project = Project.objects.get(id=project_id)
        checkpoint = Checkpoint.objects.get(project=project, checkpoint_id=checkpoint_id)
    except (Project.DoesNotExist, Checkpoint.DoesNotExist, ValueError):
        return
    notification_service.notify_verification_run(
        checkpoint, actor=request.user, scan_type=scan_type, verdict=verdict,
    )
    audit_service.record_verification_run(
        checkpoint, actor=request.user, scan_type=scan_type, verdict=verdict,
    )


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def scan_file_for_pii(request: Request) -> Response:
    """Upload a CSV file and scan it for personally identifiable information."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    # Check file type
    filename = uploaded_file.name.lower()
    if not filename.endswith('.csv'):
        return Response(
            {"error": "Only CSV files are supported for PII scanning"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check file size (max 10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        return Response(
            {"error": "File too large. Maximum size is 10MB."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response(
            {"error": "Could not read file. Please ensure it is a valid UTF-8 CSV."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Determine scan type from query param
    scan_type = request.data.get('scan_type', 'pii')
    result = scan_csv_for_pii(content)

    # For FERPA scans, add extra context
    if scan_type == 'ferpa':
        ferpa_fields = ['grade', 'enrollment', 'id_number']
        ferpa_findings = [f for f in result['findings'] if f['type'] in ferpa_fields]
        result['ferpaSpecific'] = {
            'hasFerpaData': len(ferpa_findings) > 0,
            'ferpaFindings': ferpa_findings,
            'verdict': 'Student education records detected — FERPA protections apply'
                if ferpa_findings else 'No student education record patterns detected',
        }

    verdict = 'issues found' if result.get('findings') else 'clean'
    _maybe_notify_verification(request, scan_type, verdict)

    return Response(result)


@api_view(['POST'])
def classify_data(request: Request) -> Response:
    """Suggest a data classification level based on a text description."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    description = request.data.get('description', '').strip()
    if not description:
        return Response(
            {"error": "Description is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = classify_data_from_description(description)
    verdict = str(result.get('classification', 'unknown'))
    _maybe_notify_verification(request, 'classification', verdict)
    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def bias_audit_view(request: Request) -> Response:
    """Upload a CSV and run a bias/fairness audit on it."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    if not uploaded_file.name.lower().endswith('.csv'):
        return Response({"error": "Only CSV files are supported"}, status=status.HTTP_400_BAD_REQUEST)

    if uploaded_file.size > 10 * 1024 * 1024:
        return Response({"error": "File too large. Maximum size is 10MB."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response({"error": "Could not read file. Please ensure it is a valid UTF-8 CSV."}, status=status.HTTP_400_BAD_REQUEST)

    outcome_column = request.data.get('outcome_column', '').strip()
    protected_column = request.data.get('protected_column', '').strip()
    positive_value = request.data.get('positive_value', '').strip()

    # If columns not specified, return column list for the user to select
    if not outcome_column or not protected_column:
        result = get_csv_columns(content)
        return Response(result)

    result = audit_bias(content, outcome_column, protected_column, positive_value)
    verdict = str(result.get('verdict', 'completed'))
    _maybe_notify_verification(request, 'bias', verdict)
    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def get_file_columns(request: Request) -> Response:
    """Upload a CSV and get its column names for selection dropdowns."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response({"error": "Could not read file."}, status=status.HTTP_400_BAD_REQUEST)

    result = get_csv_columns(content)
    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def redact_pii_in_file(request: Request) -> Response:
    """Upload a CSV and return a redacted copy with identity-revealing fields masked."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    filename = uploaded_file.name.lower()
    if not filename.endswith('.csv'):
        return Response(
            {"error": "Only CSV files are supported for redaction"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size > 10 * 1024 * 1024:
        return Response(
            {"error": "File too large. Maximum size is 10MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response(
            {"error": "Could not read file. Please ensure it is a valid UTF-8 CSV."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = redact_csv(content)
    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def blind_grade_csv(request: Request) -> Response:
    """Upload a CSV and return both anonymous and name-key CSVs for blind grading."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    filename = uploaded_file.name.lower()
    if not filename.endswith('.csv'):
        return Response(
            {"error": "Only CSV files are supported for blind grading"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size > 10 * 1024 * 1024:
        return Response(
            {"error": "File too large. Maximum size is 10MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        return Response(
            {"error": "Could not read file. Please ensure it is a valid UTF-8 CSV."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = pseudonymize_csv(content)
    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def extract_pdf_text(request: Request) -> Response:
    """Upload a PDF (rubric, instructions) and return its extracted text."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    filename = uploaded_file.name.lower()
    if not filename.endswith('.pdf'):
        return Response(
            {"error": "Only PDF files are supported"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size > 10 * 1024 * 1024:
        return Response(
            {"error": "File too large. Maximum size is 10MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = extract_text_from_pdf(uploaded_file.read())
    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def merge_graded_grades(request: Request) -> Response:
    """Re-attach grades to students.

    Takes the graded anonymous CSV plus the private name key and joins them on
    the per-row submission code, returning a single merged CSV with real names.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    graded_file = request.FILES.get('graded_file')
    key_file = request.FILES.get('key_file')
    if not graded_file or not key_file:
        return Response(
            {"error": "Both the graded CSV and the name key CSV are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    decoded: dict[str, str] = {}
    for label, uploaded in (('graded', graded_file), ('key', key_file)):
        if not uploaded.name.lower().endswith('.csv'):
            return Response(
                {"error": f"The {label} file must be a CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if uploaded.size > 10 * 1024 * 1024:
            return Response(
                {"error": f"The {label} file is too large. Maximum size is 10MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # utf-8-sig tolerates the BOM that Excel adds when re-saving a CSV.
            decoded[label] = uploaded.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            return Response(
                {"error": f"Could not read the {label} file. Please ensure it is a valid UTF-8 CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        result = merge_graded_with_key(decoded['graded'], decoded['key'])
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(result)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def anonymize_documents(request: Request) -> Response:
    """Anonymize a batch of student document submissions.

    Accepts a ZIP archive (field 'archive') and/or individual files (field
    'files'), plus an optional roster (field 'roster' — student names separated
    by commas or newlines). Returns the anonymized ZIP as base64 plus a private
    name-key CSV mapping each code back to its original filename.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    collected: list[tuple[str, bytes]] = []

    archive = request.FILES.get('archive')
    if archive:
        if not archive.name.lower().endswith('.zip'):
            return Response(
                {"error": "The archive must be a .zip file."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            collected.extend(read_archive(archive.read()))
        except zipfile.BadZipFile:
            return Response(
                {"error": "Could not open the ZIP file. It may be corrupt."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    for uploaded in request.FILES.getlist('files'):
        collected.append((uploaded.name, uploaded.read()))

    if not collected:
        return Response(
            {"error": "Upload a ZIP archive or one or more document files."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(collected) > MAX_DOC_COUNT:
        return Response(
            {"error": f"Too many documents ({len(collected)}). Maximum is {MAX_DOC_COUNT}."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    total_size = sum(len(data) for _, data in collected)
    if total_size > MAX_TOTAL_DOC_UPLOAD:
        return Response(
            {"error": "Documents are too large. Maximum total size is 50MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    roster_raw = request.data.get('roster', '') or ''
    roster_names = re.split(r'[\r\n,]+', roster_raw)

    try:
        result = anonymize_submissions(collected, roster_names)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'anonymizedZipBase64': base64.b64encode(result['zip_bytes']).decode('ascii'),
        'nameKeyCsv': result['name_key_csv'],
        'summary': result['summary'],
    })

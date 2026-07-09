from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from django.contrib.auth.models import User
from django.db.models import Q

from api.models import Project, Checkpoint, Decision, AITool
from api.models.project import PROJECT_CATEGORY_CHOICES

VALID_PROJECT_CATEGORIES = {value for value, _label in PROJECT_CATEGORY_CHOICES}
from api.serializers import (
    ProjectSerializer,
    CheckpointToggleResponseSerializer,
    DecisionCreateResponseSerializer,
)
from api.services import notification_service
from api.services import audit_service
from api.services.checkpoint_generator import generate_checkpoints_for_use_case
from api.services.quick_add_parser import parse_activity_description
from api.services.grading_prompt_generator import generate_grading_prompt
from api.services.smart_defaults import generate_smart_defaults
from api.serializers.project import infer_risk_context


def get_user_projects(user):
    """Get projects owned by user OR where user is faculty advisor or student collaborator."""
    return Project.objects.filter(
        Q(user=user) | Q(faculty_advisor=user) | Q(student_collaborator=user)
    ).distinct().order_by('-created_at')


def user_can_access_project(user, project):
    """Check if user owns, advises, or collaborates on this project."""
    return project.user == user or project.faculty_advisor == user or project.student_collaborator == user


def serialize_project(project: Project) -> dict:
    """Serialize a project in the camelCase format the frontend expects."""
    return ProjectSerializer(project).data


@api_view(['GET', 'POST'])
def project_list_create(request: Request) -> Response:
    """List all projects for the user, or create a new one."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        projects = get_user_projects(request.user)
        return Response([serialize_project(p) for p in projects])

    # POST -- create
    name = request.data.get('name', '').strip()
    ai_use_case = request.data.get('ai_use_case', '')

    if not name:
        return Response({"error": "Project name is required"}, status=status.HTTP_400_BAD_REQUEST)

    raw_category = request.data.get('category')
    category = raw_category.strip() if isinstance(raw_category, str) and raw_category.strip() else None
    if category is not None and category not in VALID_PROJECT_CATEGORIES:
        return Response(
            {"error": f"Invalid category. Must be one of: {', '.join(sorted(VALID_PROJECT_CATEGORIES))}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Look up faculty advisor by email if provided
    faculty_advisor = None
    advisor_email = request.data.get('faculty_advisor_email', '').strip().lower()
    if advisor_email:
        try:
            faculty_advisor = User.objects.get(email=advisor_email)
        except User.DoesNotExist:
            pass

    # Look up student collaborator by email if provided
    student_collab = None
    student_email = request.data.get('student_collaborator_email', '').strip().lower()
    if student_email:
        try:
            student_collab = User.objects.get(email=student_email)
        except User.DoesNotExist:
            pass

    project = Project.objects.create(
        user=request.user,
        name=name,
        description=request.data.get('description', ''),
        ai_use_case=ai_use_case,
        category=category,
        faculty_advisor=faculty_advisor,
        student_collaborator=student_collab,
        share_as_example=bool(request.data.get('share_as_example', False)),
    )

    # Generate checkpoints based on use case + risk context
    risk_context = request.data.get('risk_context', {})
    checkpoint_defs = generate_checkpoints_for_use_case(ai_use_case, risk_context)
    for cp_def in checkpoint_defs:
        Checkpoint.objects.create(project=project, **cp_def)

    # Link AI tools if provided
    ai_tool_ids = request.data.get('ai_tool_ids', [])
    if ai_tool_ids:
        tools = AITool.objects.filter(id__in=ai_tool_ids)
        project.ai_tools.set(tools)

    audit_service.record_activity_created(project, actor=request.user)

    return Response(serialize_project(project), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def project_detail(request: Request, project_id: int) -> Response:
    """Get, update, or delete a single project."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        if project.user != request.user:
            return Response(
                {"error": "Only the activity owner can delete this activity."},
                status=status.HTTP_403_FORBIDDEN,
            )
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == 'PUT':
        # Snapshot mutable fields so we can log exactly what changed.
        original = {
            'name': project.name,
            'description': project.description,
            'category': project.category,
            'share_as_example': project.share_as_example,
            'faculty_advisor_id': project.faculty_advisor_id,
            'student_collaborator_id': project.student_collaborator_id,
        }

        # Only owner can edit name/description, category, and share-as-example flag
        if project.user == request.user:
            if 'name' in request.data:
                project.name = request.data['name'].strip()
            if 'description' in request.data:
                project.description = request.data['description']
            if 'category' in request.data:
                raw_category = request.data.get('category')
                if isinstance(raw_category, str) and raw_category.strip():
                    new_category = raw_category.strip()
                    if new_category not in VALID_PROJECT_CATEGORIES:
                        return Response(
                            {"error": f"Invalid category. Must be one of: {', '.join(sorted(VALID_PROJECT_CATEGORIES))}"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    project.category = new_category
                else:
                    project.category = None
            if 'share_as_example' in request.data:
                project.share_as_example = bool(request.data['share_as_example'])

        # Owner can set/change faculty advisor
        faculty_email = request.data.get('faculty_advisor_email', '').strip().lower()
        if faculty_email and project.user == request.user:
            try:
                advisor = User.objects.get(email=faculty_email)
                project.faculty_advisor = advisor
            except User.DoesNotExist:
                return Response({"error": f"No account found for {faculty_email}"}, status=status.HTTP_400_BAD_REQUEST)
        elif faculty_email == '' and 'faculty_advisor_email' in request.data:
            project.faculty_advisor = None

        # Owner can set/change student collaborator
        student_email = request.data.get('student_collaborator_email', '').strip().lower()
        if student_email and project.user == request.user:
            try:
                student = User.objects.get(email=student_email)
                project.student_collaborator = student
            except User.DoesNotExist:
                return Response({"error": f"No account found for {student_email}"}, status=status.HTTP_400_BAD_REQUEST)
        elif student_email == '' and 'student_collaborator_email' in request.data:
            project.student_collaborator = None

        # Handle risk context changes — backfill any missing checkpoints
        risk_context = request.data.get('risk_context')
        if risk_context and project.user == request.user:
            expected = generate_checkpoints_for_use_case(project.ai_use_case, risk_context)
            existing_ids = set(project.checkpoints.values_list('checkpoint_id', flat=True))
            added = 0
            for cp_def in expected:
                if cp_def['checkpoint_id'] not in existing_ids:
                    Checkpoint.objects.create(project=project, **cp_def)
                    added += 1
            # Also remove checkpoints that are no longer needed AND not yet completed
            expected_ids = {cp['checkpoint_id'] for cp in expected}
            for cp in project.checkpoints.filter(completed=False):
                if cp.checkpoint_id not in expected_ids:
                    cp.delete()

        project.save()

        # Log what changed. Share-as-example gets its own event type; the
        # other editable fields collapse into a single "activity updated".
        changed_fields: list[str] = []
        if project.name != original['name']:
            changed_fields.append('name')
        if project.description != original['description']:
            changed_fields.append('description')
        if project.category != original['category']:
            changed_fields.append('category')
        if project.faculty_advisor_id != original['faculty_advisor_id']:
            changed_fields.append('faculty advisor')
        if project.student_collaborator_id != original['student_collaborator_id']:
            changed_fields.append('student collaborator')
        if changed_fields:
            audit_service.record_activity_updated(
                project, actor=request.user, changed_fields=changed_fields,
            )
        if project.share_as_example != original['share_as_example']:
            audit_service.record_share_toggled(
                project, actor=request.user, shared=project.share_as_example,
            )

        return Response(serialize_project(project))

    return Response(serialize_project(project))


@api_view(['PUT'])
def checkpoint_toggle(request: Request, project_id: int, checkpoint_id: str) -> Response:
    """Toggle a checkpoint's completed status."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        checkpoint = Checkpoint.objects.get(project=project, checkpoint_id=checkpoint_id)
    except Checkpoint.DoesNotExist:
        return Response({"error": "Checkpoint not found"}, status=status.HTTP_404_NOT_FOUND)

    checkpoint.completed = not checkpoint.completed
    checkpoint.completed_at = timezone.now() if checkpoint.completed else None
    checkpoint.save()

    if checkpoint.completed:
        notification_service.notify_checkpoint_completed(checkpoint, actor=request.user)
        audit_service.record_checkpoint_completed(checkpoint, actor=request.user)
    else:
        audit_service.record_checkpoint_reopened(checkpoint, actor=request.user)

    return Response(CheckpointToggleResponseSerializer(checkpoint).data)


@api_view(['POST'])
def decision_create(request: Request, project_id: int) -> Response:
    """Log a decision for a checkpoint."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    checkpoint_id = request.data.get('checkpoint')
    description = request.data.get('description', '').strip()

    if not checkpoint_id or not description:
        return Response(
            {"error": "checkpoint and description are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        checkpoint = Checkpoint.objects.get(project=project, checkpoint_id=checkpoint_id)
    except Checkpoint.DoesNotExist:
        return Response({"error": "Checkpoint not found"}, status=status.HTTP_404_NOT_FOUND)

    # Resolve tool_used if provided
    tool_used = None
    tool_used_id = request.data.get('toolUsedId')
    if tool_used_id:
        try:
            tool_used = AITool.objects.get(id=tool_used_id)
        except AITool.DoesNotExist:
            pass

    decision = Decision.objects.create(
        project=project,
        checkpoint=checkpoint,
        description=description,
        notes=request.data.get('notes', ''),
        proof_type=request.data.get('proofType', ''),
        proof_value=request.data.get('proofValue', ''),
        tool_used=tool_used,
    )

    audit_service.record_decision_logged(decision, actor=request.user)

    # Auto-complete the checkpoint if not already
    if not checkpoint.completed:
        checkpoint.completed = True
        checkpoint.completed_at = timezone.now()
        checkpoint.save()
        decision.refresh_from_db(fields=['checkpoint'])
        notification_service.notify_checkpoint_completed(checkpoint, actor=request.user)
        audit_service.record_checkpoint_completed(checkpoint, actor=request.user)

    return Response(
        DecisionCreateResponseSerializer(decision).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
def quick_add_parse(request: Request) -> Response:
    """Parse a free-text description into a draft activity.

    Returns the parsed fields (use case, risk context, suggested tools, name)
    without saving anything. The client confirms and the existing
    project_list_create endpoint persists the activity.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    description = (request.data.get('description') or '').strip()
    if not description:
        return Response({"error": "Description is required"}, status=status.HTTP_400_BAD_REQUEST)

    available_tools = list(AITool.objects.values('id', 'name'))
    draft = parse_activity_description(description, available_tools)
    return Response(draft)


@api_view(['POST'])
def grading_prompt_view(request: Request, project_id: int) -> Response:
    """Generate a grading prompt for the activity's AI tool, with built-in guardrails."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    rubric_text = (request.data.get('rubric_text') or '').strip()
    if not rubric_text:
        return Response({"error": "rubric_text is required"}, status=status.HTTP_400_BAD_REQUEST)

    ai_tool_name = (request.data.get('ai_tool_name') or '').strip() or None
    if not ai_tool_name:
        first_tool = project.ai_tools.first()
        if first_tool:
            ai_tool_name = first_tool.name

    checkpoint_ids = set(project.checkpoints.values_list('checkpoint_id', flat=True))
    risk_context = infer_risk_context(checkpoint_ids)

    result = generate_grading_prompt(
        activity_name=project.name,
        activity_description=project.description or '',
        rubric_text=rubric_text,
        risk_context=risk_context,
        ai_tool_name=ai_tool_name,
    )
    return Response(result)


@api_view(['GET'])
def smart_defaults_view(request: Request, project_id: int) -> Response:
    """Return draft attestations for incomplete non-scannable checkpoints."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    checkpoint_ids = set(project.checkpoints.values_list('checkpoint_id', flat=True))
    risk_context = infer_risk_context(checkpoint_ids)
    tool_names = list(project.ai_tools.values_list('name', flat=True))

    incomplete = list(
        project.checkpoints
        .filter(completed=False)
        .values('checkpoint_id', 'label')
    )

    drafts = generate_smart_defaults(
        use_case=project.ai_use_case,
        risk_context=risk_context,
        tools=tool_names,
        incomplete_checkpoints=incomplete,
    )
    return Response({'drafts': drafts})


@api_view(['GET'])
def activity_library(request: Request) -> Response:
    """Return de-identified activity summaries for the institutional Use Cases library."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    use_case_filter = request.query_params.get('use_case', '').strip()
    tool_filter = request.query_params.get('tool', '').strip()

    qs = Project.objects.filter(share_as_example=True).prefetch_related('ai_tools', 'checkpoints')
    if use_case_filter:
        qs = qs.filter(ai_use_case=use_case_filter)
    if tool_filter:
        qs = qs.filter(ai_tools__name__iexact=tool_filter)

    qs = qs.order_by('-created_at').distinct()

    items: list[dict] = []
    for p in qs:
        checkpoints = list(p.checkpoints.all())
        total = len(checkpoints)
        completed = sum(1 for c in checkpoints if c.completed)
        items.append({
            'id': p.id,
            'name': p.name,
            'description': p.description or '',
            'aiUseCase': p.ai_use_case,
            'tools': list(p.ai_tools.values_list('name', flat=True)),
            'completedCount': completed,
            'totalCount': total,
            'completionPct': round(100 * completed / total) if total else 0,
            'createdAt': p.created_at.isoformat(),
        })

    return Response({'items': items, 'totalCount': len(items)})


@api_view(['GET'])
def activity_library_detail(request: Request, project_id: int) -> Response:
    """Return a read-only de-identified view of a single shared activity."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id, share_as_example=True)
    except Project.DoesNotExist:
        return Response({"error": "Use case not found"}, status=status.HTTP_404_NOT_FOUND)

    checkpoint_ids = set(project.checkpoints.values_list('checkpoint_id', flat=True))
    risk_context = infer_risk_context(checkpoint_ids)

    completed_checkpoints = [
        {
            'id': c.checkpoint_id,
            'label': c.label,
            'category': c.category,
            'completedAt': c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in project.checkpoints.filter(completed=True).order_by('category', 'label')
    ]

    pending_checkpoints = [
        {
            'id': c.checkpoint_id,
            'label': c.label,
            'category': c.category,
        }
        for c in project.checkpoints.filter(completed=False).order_by('category', 'label')
    ]

    return Response({
        'id': project.id,
        'name': project.name,
        'description': project.description or '',
        'aiUseCase': project.ai_use_case,
        'tools': list(project.ai_tools.values_list('name', flat=True)),
        'riskContext': risk_context,
        'completedCheckpoints': completed_checkpoints,
        'pendingCheckpoints': pending_checkpoints,
        'createdAt': project.created_at.isoformat(),
    })

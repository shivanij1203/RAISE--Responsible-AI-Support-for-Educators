from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from django.contrib.auth.models import User
from django.db.models import Q

from api.models import Project, Checkpoint, Decision, AITool
from api.serializers import (
    ProjectSerializer,
    CheckpointToggleResponseSerializer,
    DecisionCreateResponseSerializer,
)
from api.services import notification_service
from api.services.checkpoint_generator import generate_checkpoints_for_use_case


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
        faculty_advisor=faculty_advisor,
        student_collaborator=student_collab,
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

    return Response(serialize_project(project), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT'])
def project_detail(request: Request, project_id: int) -> Response:
    """Get or update a single project."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        # Only owner can edit name/description
        if project.user == request.user:
            if 'name' in request.data:
                project.name = request.data['name'].strip()
            if 'description' in request.data:
                project.description = request.data['description']

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

    # Auto-complete the checkpoint if not already
    if not checkpoint.completed:
        checkpoint.completed = True
        checkpoint.completed_at = timezone.now()
        checkpoint.save()
        decision.refresh_from_db(fields=['checkpoint'])
        notification_service.notify_checkpoint_completed(checkpoint, actor=request.user)

    return Response(
        DecisionCreateResponseSerializer(decision).data,
        status=status.HTTP_201_CREATED,
    )

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.models import Project, Checkpoint, CheckpointComment
from api.serializers import CheckpointCommentSerializer
from api.services import notification_service
from api.services import audit_service


@api_view(['GET', 'POST'])
def checkpoint_comments(request: Request, project_id: int, checkpoint_id: str) -> Response:
    """List or create comments on a checkpoint."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        checkpoint = Checkpoint.objects.get(project=project, checkpoint_id=checkpoint_id)
    except Checkpoint.DoesNotExist:
        return Response({"error": "Checkpoint not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        comments = checkpoint.comments.select_related('user', 'user__profile').all()
        return Response(CheckpointCommentSerializer(comments, many=True).data)

    # POST
    text = request.data.get('text', '').strip()
    if not text:
        return Response({"error": "Comment text is required"}, status=status.HTTP_400_BAD_REQUEST)

    comment = CheckpointComment.objects.create(
        checkpoint=checkpoint,
        user=request.user,
        text=text,
    )
    notification_service.notify_comment_added(comment)
    audit_service.record_comment_added(comment)
    return Response(
        CheckpointCommentSerializer(comment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
def checkpoint_comment_resolve(request: Request, project_id: int, checkpoint_id: str, comment_id: int) -> Response:
    """Toggle the resolved state of a comment.

    Body: {"resolved": true|false}. Any user with project access can mark
    or reopen. The audit record stamps resolved_at and resolved_by.
    """
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        checkpoint = Checkpoint.objects.get(project=project, checkpoint_id=checkpoint_id)
    except Checkpoint.DoesNotExist:
        return Response({"error": "Checkpoint not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        comment = checkpoint.comments.get(id=comment_id)
    except CheckpointComment.DoesNotExist:
        return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

    new_state = bool(request.data.get('resolved', True))
    comment.resolved = new_state
    if new_state:
        comment.resolved_at = timezone.now()
        comment.resolved_by = request.user
    else:
        comment.resolved_at = None
        comment.resolved_by = None
    comment.save()
    audit_service.record_comment_resolved(
        comment, actor=request.user, resolved=new_state,
    )
    return Response(CheckpointCommentSerializer(comment).data)

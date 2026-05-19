"""Activity timeline endpoint — the read side of the audit log."""
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.models import Project
from api.serializers import ActivityEventSerializer
from api.views.projects import user_can_access_project

# Cap the response so a long-lived activity can't return an unbounded payload.
MAX_TIMELINE_EVENTS = 200


@api_view(['GET'])
def project_timeline(request: Request, project_id: int) -> Response:
    """Return the chronological audit log for an activity (newest first)."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(request.user, project):
        return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

    events = (
        project.events
        .select_related('actor', 'checkpoint')
        .all()[:MAX_TIMELINE_EVENTS]
    )
    return Response(ActivityEventSerializer(events, many=True).data)

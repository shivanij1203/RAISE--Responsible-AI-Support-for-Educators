from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.models import Notification
from api.serializers.notification import NotificationSerializer


@api_view(['GET'])
def notification_list(request: Request) -> Response:
    """List current user's notifications, newest first, with unread count."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    qs = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related('actor', 'project', 'checkpoint')
    )
    unread_count = qs.filter(read=False).count()
    return Response({
        "unreadCount": unread_count,
        "notifications": NotificationSerializer(qs, many=True).data,
    })


@api_view(['POST'])
def notification_mark_read(request: Request, notification_id: int) -> Response:
    """Mark a single notification as read."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        notif = Notification.objects.get(id=notification_id, recipient=request.user)
    except Notification.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    notif.read = True
    notif.save(update_fields=['read'])
    return Response({"ok": True})


@api_view(['POST'])
def notification_mark_all_read(request: Request) -> Response:
    """Mark all of the current user's notifications as read."""
    if not request.user.is_authenticated:
        return Response({"error": "Not logged in"}, status=status.HTTP_401_UNAUTHORIZED)

    updated = Notification.objects.filter(
        recipient=request.user, read=False,
    ).update(read=True)
    return Response({"ok": True, "updated": updated})

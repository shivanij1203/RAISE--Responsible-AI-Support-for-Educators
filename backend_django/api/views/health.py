import logging

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from django.db import connection

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    """Lightweight health check for uptime monitors and keep-warm pings.

    Always returns HTTP 200 so an external monitor can keep the Render web
    process awake. A trivial query keeps the database connection warm too;
    a database error is reported in the body and logged server-side rather
    than failing the response.
    """
    database = 'ok'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as exc:  # noqa: BLE001 - health probe must never raise
        database = 'unavailable'
        logger.warning('Health check database probe failed: %s', exc)

    return Response({'status': 'ok', 'database': database})

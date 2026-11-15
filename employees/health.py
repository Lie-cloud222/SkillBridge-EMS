import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
@never_cache
def health_check(request):
    """Used by uptime monitors and Render's health check.

    Returns 200 when the app can reach its database, otherwise 503.
    Reveals no configuration or data, so it needs no login.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        logger.exception('Health check failed: database unreachable')
        return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})

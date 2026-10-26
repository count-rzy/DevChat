from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    try:
        connection.ensure_connection()
        database_status = "connected"
    except Exception:
        database_status = "error"

    status_code = 200 if database_status == "connected" else 503

    return JsonResponse(
        {
            "status": "ok" if status_code == 200 else "error",
            "database": database_status,
        },
        status=status_code,
    )
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.api")


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    Provides a consistent error structure for all API errors.
    """
    # 1. Handle our custom application exceptions FIRST
    # We check for 'code' and 'message' attributes which our AlloRouteError has
    code = getattr(exc, "code", None)
    message = getattr(exc, "message", None)

    if code is not None and message is not None:
        details = getattr(exc, "details", {})
        data = {"error": {"code": code, "message": message, "details": details}}

        # Map exception types to status codes
        # We use class name to avoid identity issues with multiple imports
        status_code = status.HTTP_400_BAD_REQUEST
        exc_class_name = exc.__class__.__name__

        if exc_class_name == "ResourceNotFoundError" or "NotFound" in exc_class_name:
            status_code = status.HTTP_404_NOT_FOUND
        elif exc_class_name == "ServiceTimeoutError" or "Timeout" in exc_class_name:
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif (
            exc_class_name == "ServiceUnavailableError"
            or "Unavailable" in exc_class_name
        ):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(data, status=status_code)

    # 2. Call DRF's default exception handler for standard DRF errors
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize DRF error response
        # Most tests expect the status code as the error code for DRF exceptions
        response.data = {
            "error": {
                "code": response.status_code,
                "message": str(exc),
                "details": response.data,
            }
        }
        return response

    # 3. Handle everything else as a 500
    logger.exception(f"Unhandled Exception: {exc}")
    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred.",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

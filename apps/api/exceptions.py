import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.api")


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    Provides a consistent error structure for all API errors.
    """
    # 1. Handle standard DRF ValidationError first so the API shape is always consistent.
    if isinstance(exc, DRFValidationError):
        detail = getattr(exc, "detail", None)
        message = detail if detail is not None else str(exc)
        return Response(
            {
                "error": {
                    "code": "validation_error",
                    "message": message,
                    "details": detail,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Handle our custom application exceptions next.
    code = getattr(exc, "code", None)
    message = getattr(exc, "message", None)

    if code is not None and message is not None:
        details = getattr(exc, "details", {})
        data = {"error": {"code": code, "message": message, "details": details}}

        # Map exception types to status codes
        status_code = status.HTTP_400_BAD_REQUEST
        
        # Explicit check for known exception names that might not be instances
        exc_class_name = exc.__class__.__name__

        if "NotFound" in exc_class_name:
            status_code = status.HTTP_404_NOT_FOUND
        elif "Timeout" in exc_class_name:
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif "Unavailable" in exc_class_name:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(data, status=status_code)

    # 2. Call DRF's default exception handler for standard DRF errors
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize DRF error response
        # If response.data is a dict, it might be the DRF detail structure
        message = str(exc)
        if isinstance(response.data, dict) and "detail" in response.data:
             message = response.data["detail"]
        
        response.data = {
            "error": {
                "code": response.status_code,
                "message": message,
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

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger("apps.api")

def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    Provides a consistent error structure for all API errors.
    """
    # print(f"DEBUG: custom_exception_handler called for {type(exc)}")
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize the error response
        if isinstance(response.data, dict):
            response.data = {
                "error": {
                    "code": response.status_code,
                    "message": str(exc),
                    "details": response.data
                }
            }
        else:
            response.data = {
                "error": {
                    "code": response.status_code,
                    "message": str(exc),
                    "details": {"info": response.data}
                }
            }
    else:
        # Handle custom application exceptions
        from apps.common.exceptions import AlloRouteError
        
        if isinstance(exc, AlloRouteError):
            response = Response(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details
                    }
                },
                status=status.HTTP_400_BAD_REQUEST # Default for logic errors
            )
            
            # Map specific exceptions to status codes
            from apps.common.exceptions import (
                ResourceNotFoundError, 
                ValidationError, 
                ServiceTimeoutError, 
                ServiceUnavailableError
            )
            if isinstance(exc, ResourceNotFoundError):
                response.status_code = status.HTTP_404_NOT_FOUND
            elif isinstance(exc, ValidationError):
                response.status_code = status.HTTP_400_BAD_REQUEST
            elif isinstance(exc, ServiceTimeoutError):
                response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
            elif isinstance(exc, ServiceUnavailableError):
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            # For unhandled exceptions, log the full traceback and return 500
            logger.exception(f"Unhandled Exception: {exc}")
            response = Response(
                {
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred."
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return response

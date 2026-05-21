import uuid
import threading
import time
import logging
from typing import Callable
from django.http import HttpRequest, HttpResponse

# Thread-local storage for correlation ID
_storage = threading.local()
logger = logging.getLogger("infrastructure.logging")

def get_correlation_id() -> str:
    """Retrieve the correlation ID for the current thread."""
    return getattr(_storage, "correlation_id", "no-id")

class CorrelationIdMiddleware:
    """
    Middleware that assigns a unique correlation ID to every request.
    This ID is used to link all log entries related to a single request.
    """
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check if the ID was passed from an upstream service
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Store in thread-local for logging
        _storage.correlation_id = correlation_id
        
        response = self.get_response(request)
        
        # Return the ID in the response for debugging
        response["X-Correlation-ID"] = correlation_id
        
        # Cleanup
        if hasattr(_storage, "correlation_id"):
            del _storage.correlation_id
            
        return response

class RequestLoggingMiddleware:
    """
    Middleware that logs request details and response status/timing.
    """
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.get_full_path()}",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
            }
        )
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log request completion
        logger.info(
            f"Request finished: {request.method} {request.get_full_path()} - {response.status_code} ({duration:.3f}s)",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_sec": duration,
            }
        )
        
        return response

class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that injects the correlation_id into the log record.
    """
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True

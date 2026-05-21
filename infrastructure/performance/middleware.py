import time
import logging
from typing import Callable
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("infrastructure.performance")

class PerformanceMetricsMiddleware:
    """
    Middleware to track request execution time and log performance metrics.
    """
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Add header for transparency (Internal use/debugging)
        response["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        
        if duration_ms > 500:
            logger.warning(
                f"Slow Request: {request.method} {request.path} took {duration_ms:.2f}ms"
            )
        else:
            logger.info(
                f"Request: {request.method} {request.path} took {duration_ms:.2f}ms"
            )
            
        return response

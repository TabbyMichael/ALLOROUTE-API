import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from infrastructure.logging.utils import thread_local

logger = logging.getLogger("infrastructure.logging")

class CorrelationIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        thread_local.correlation_id = correlation_id
        request.correlation_id = correlation_id

    def process_response(self, request, response):
        response["X-Correlation-ID"] = getattr(request, "correlation_id", "no-id")
        return response

class AuditLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method not in ["GET", "OPTIONS", "HEAD"]:
            # Uses correlation_id from CorrelationIdMiddleware
            corr_id = getattr(request, "correlation_id", "no-id")
            # Logic here...
            pass
        return None

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        duration = (time.time() - getattr(request, "start_time", time.time())) * 1000
        logger.info(f"REQUEST | {request.method} {request.path} | {response.status_code} | {duration:.2f}ms")
        return response

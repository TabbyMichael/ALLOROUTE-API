import hashlib
import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("infrastructure.performance")

class IdempotencyMiddleware(MiddlewareMixin):
    """
    Middleware to handle idempotency for POST requests.
    Expects 'X-Idempotency-Key' header.
    """
    def process_request(self, request):
        if request.method == "POST":
            key = request.headers.get("X-Idempotency-Key")
            if key:
                user = getattr(request, "user", None)
                user_id = user.id if user and getattr(user, "is_authenticated", False) else "anon"
                method = request.method.upper()
                path = getattr(request, "path", "")
                body = getattr(request, "body", b"")
                if isinstance(body, str):
                    body = body.encode(request.encoding or "utf-8")
                elif isinstance(body, memoryview):
                    body = body.tobytes()

                try:
                    body_hash = hashlib.sha256(body).hexdigest() if body else ""
                except Exception:
                    body_hash = ""

                cache_key = f"idempotency:{user_id}:{key}:{method}:{path}:{body_hash}"

                cached_response = cache.get(cache_key)
                if cached_response:
                    logger.debug(f"Cache HIT for key: {cache_key}")
                    response = HttpResponse(
                        cached_response["body"],
                        content_type=cached_response.get("content_type"),
                        status=cached_response["status"],
                    )
                    for header_name, header_value in cached_response.get("headers", {}).items():
                        if header_name.lower() in (
                            "content-length",
                            "date",
                            "server",
                            "set-cookie",
                            "authorization",
                            "cookie",
                        ):
                            continue
                        response[header_name] = header_value
                    return response

                logger.debug(f"Cache MISS for key: {cache_key}")
                request.idempotency_key = cache_key
        return None

    def process_response(self, request, response):
        if hasattr(request, "idempotency_key") and response.status_code == 200:
            content_type = response.get("Content-Type", "")
            if content_type.startswith("application/json"):
                content = response.content
                if isinstance(content, str):
                    content = content.encode(response.charset or "utf-8")

                max_cacheable_bytes = getattr(settings, "IDEMPOTENCY_MAX_CACHE_BYTES", 1024 * 1024)
                if len(content) <= max_cacheable_bytes:
                    cache_payload = {
                        "body": content,
                        "status": response.status_code,
                        "content_type": content_type,
                        "headers": dict(response.items()),
                    }
                    cache.set(
                        request.idempotency_key,
                        cache_payload,
                        timeout=getattr(settings, "IDEMPOTENCY_CACHE_TIMEOUT", 3600),
                    )
        return response

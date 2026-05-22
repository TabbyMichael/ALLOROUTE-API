import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger("infrastructure.logging.instrumentation")


def time_execution(name: str = None):
    """
    Decorator that logs the execution time of a function.
    Useful for service-level instrumentation.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"Operation '{operation_name}' completed",
                    extra={
                        "operation": operation_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "success",
                    },
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation '{operation_name}' failed after {duration_ms:.2f}ms: {str(e)}",
                    extra={
                        "operation": operation_name,
                        "duration_ms": round(duration_ms, 2),
                        "status": "error",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        return wrapper

    return decorator

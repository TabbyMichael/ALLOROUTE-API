import logging
import time
import threading
from functools import wraps

thread_local = threading.local()

class CorrelationIdFilter(logging.Filter):
    """
    Filter that injects a correlation ID into the log record.
    """
    def filter(self, record):
        record.correlation_id = getattr(thread_local, "correlation_id", "no-id")
        return True

def get_correlation_id():
    return getattr(thread_local, "correlation_id", "no-id")


def time_execution(name: str):
    """
    Decorator to log execution time of a function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            logging.getLogger("infrastructure.performance").info(
                f"EXECUTION_TIME | {name} | {duration:.2f}ms"
            )
            return result
        return wrapper
    return decorator

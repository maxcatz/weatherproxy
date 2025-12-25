import time
import structlog
import functools
from typing import Callable, Any, Awaitable

log = structlog.get_logger(__name__)

def log_metrics(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """
    Decorator to log execution time and, optionally, response status code for async functions.
    Works with functions that return httpx.Response or any dict-like object.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = await func(*args, **kwargs)
        duration = time.monotonic() - start

        # If result is an httpx.Response, log status code
        status = getattr(result, "status_code", None)

        # Log with function name, duration, and optional status
        if status is not None:
            log.info("%s executed in %.3f s with status=%s", func.__name__, duration, status)
        else:
            log.info("%s executed in %.3f s", func.__name__, duration)
        return result

    return wrapper

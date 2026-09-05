"""
Simple Redis-backed fixed-window rate limiter.

Applied to auth endpoints (login/register) and AI-triggering endpoints,
which are the most sensitive to abuse (credential stuffing, quota burn on
the AI provider). Uses INCR + EXPIRE so it's cheap and works correctly
across multiple backend processes/workers, unlike an in-memory counter.
"""
from fastapi import Request

from app.core.redis import get_redis
from app.common.exceptions import RateLimitError


def rate_limit(key_prefix: str, max_requests: int, window_seconds: int):
    """Returns a FastAPI dependency that rate-limits by client IP.

    Usage: Depends(rate_limit("login", max_requests=10, window_seconds=60))
    """

    def _dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        redis_key = f"ratelimit:{key_prefix}:{client_ip}"

        try:
            client = get_redis()
            current = client.incr(redis_key)
            if current == 1:
                client.expire(redis_key, window_seconds)
        except Exception:
            # If Redis is unavailable, fail open rather than taking the API
            # down over a non-critical dependency - correctness of the core
            # product must not depend on the rate limiter being reachable.
            return

        if current > max_requests:
            raise RateLimitError(
                f"Too many requests. Please wait a moment and try again.",
            )

    return _dependency

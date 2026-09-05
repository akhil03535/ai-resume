import json
import logging
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger("resumeai.redis")

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
    return _redis_client


def cache_set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    """Store a JSON-serializable value with an expiry. Used to avoid re-calling
    the AI provider for identical resume/JD text (see AI cost control, spec #35).

    Caching is a performance/cost optimization, not a correctness requirement -
    a Redis outage must degrade to "just don't cache this", never crash the
    request or masquerade as an AI failure (spec: 'Redis failure must not
    produce misleading AI service unavailable errors')."""
    try:
        client = get_redis()
        client.set(key, json.dumps(value), ex=ttl_seconds)
    except redis.RedisError as exc:
        logger.warning("Redis cache_set failed (continuing without caching this response): %s", exc)


def cache_get(key: str) -> Optional[Any]:
    try:
        client = get_redis()
        raw = client.get(key)
    except redis.RedisError as exc:
        logger.warning("Redis cache_get failed (treating as cache miss, calling AI provider directly): %s", exc)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Redis returned a corrupted cache entry for key=%s; ignoring it.", key)
        return None

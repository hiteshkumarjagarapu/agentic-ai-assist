"""Redis conversation buffer (last N messages per session) + final-answer cache.

All operations degrade gracefully: if Redis is unavailable, callers fall back to MySQL.
"""
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from config import settings

log = logging.getLogger(__name__)
BUFFER_SIZE = 10
BUFFER_TTL = 24 * 3600

_redis: Optional[aioredis.Redis] = None


def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is None and settings.REDIS_URL:
        _redis = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True, socket_timeout=3, socket_connect_timeout=3
        )
    return _redis


async def get_buffer(session_id: str) -> Optional[list[dict]]:
    """Return buffered messages, or None if Redis is unavailable / empty."""
    r = get_redis()
    if r is None:
        return None
    try:
        raw = await r.lrange(f"chat:{session_id}", -BUFFER_SIZE, -1)
        return [json.loads(x) for x in raw] or None
    except Exception as e:
        log.warning("redis get_buffer failed: %s", e)
        return None


async def append_buffer(session_id: str, role: str, content: str) -> None:
    r = get_redis()
    if r is None:
        return
    key = f"chat:{session_id}"
    try:
        await r.rpush(key, json.dumps({"role": role, "content": content}))
        await r.ltrim(key, -BUFFER_SIZE, -1)
        await r.expire(key, BUFFER_TTL)
    except Exception as e:
        log.warning("redis append_buffer failed: %s", e)


async def cache_answer(session_id: str, answer: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        await r.set(f"answer:{session_id}", answer, ex=settings.CACHE_TTL)
    except Exception as e:
        log.warning("redis cache_answer failed: %s", e)

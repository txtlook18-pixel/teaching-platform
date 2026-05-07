import json
import hashlib
import redis.asyncio as aioredis
from typing import Any, Optional

from app.config import settings


_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis


def _make_key(prefix: str, **kwargs) -> str:
    raw = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"ai:{prefix}:{digest}"


async def get_cached(prefix: str, **kwargs) -> Optional[Any]:
    if not settings.use_cache:
        return None
    try:
        r = await get_redis()
        key = _make_key(prefix, **kwargs)
        value = await r.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


async def set_cached(prefix: str, data: Any, ttl: int = None, **kwargs) -> None:
    if not settings.use_cache:
        return
    try:
        r = await get_redis()
        key = _make_key(prefix, **kwargs)
        await r.set(key, json.dumps(data, ensure_ascii=False), ex=ttl or settings.cache_ttl)
    except Exception:
        pass

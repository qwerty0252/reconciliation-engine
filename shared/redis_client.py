import redis.asyncio as aioredis
from redis.asyncio import Redis

from config.settings import get_settings

settings = get_settings()

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None

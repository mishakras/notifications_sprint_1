import redis.asyncio as redis
from src.core import settings

redis_client: redis.Redis = None


async def get_redis() -> redis.Redis:
    """Получение Redis клиента"""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            decode_responses=True,
        )
    return redis_client


async def close_redis():
    """Закрытие Redis соединения"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

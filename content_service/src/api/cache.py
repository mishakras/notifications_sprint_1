import hashlib
import json
from functools import wraps
from typing import Callable

from pydantic import BaseModel

from content_service.src.db.redis import Redis, get_redis


def cache(expire: int):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis: Redis = await get_redis()

            # Генерация ключа кеша
            sorted_kwargs = {k: kwargs[k] for k in sorted(kwargs)}
            key_data = f"{func.__name__}:{args}:{sorted_kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Проверяем наличие данных в кеше
            cached_data = await redis.get(cache_key)
            if cached_data:
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode("utf-8")
                return json.loads(cached_data)

            # Если в кеше нет, вызываем функцию
            result = await func(*args, **kwargs)

            # Если результат — Pydantic модель, преобразуем в словарь
            if isinstance(result, BaseModel):
                result = result.dict()

            # Сохраняем результат в кеш
            await redis.set(cache_key, json.dumps(result), ex=expire)
            return result

        return wrapper

    return decorator

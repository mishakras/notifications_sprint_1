import hashlib
import json
from datetime import date, datetime
from functools import wraps
from typing import Callable
from uuid import UUID

from pydantic import BaseModel

from mongo_db_user_api.src.db.redis import Redis, get_redis


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

            # Улучшенный сериализатор для JSON
            def default_serializer(obj):
                if isinstance(obj, (UUID, datetime, date)):
                    return str(obj)
                elif hasattr(obj, "dict"):
                    return obj.dict()
                raise TypeError(
                    f"Object of type {obj.__class__.__name__} is not JSON serializable",  # noqa: E501
                )

            # Сохраняем результат в кеш
            await redis.set(
                cache_key,
                json.dumps(
                    result,
                    default=default_serializer,
                    ensure_ascii=False,
                ),
                ex=expire,
            )
            return result

        return wrapper

    return decorator

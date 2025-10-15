import hashlib
import json
from functools import wraps
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

from pydantic import BaseModel

from recommendation.src.db.redis import Redis, get_redis

FuncParams = ParamSpec("FuncParams")  # сохраняем сигнатуру через ParamSpec
ReturnT = TypeVar("ReturnT")  # тип возвращаемого значения

# алиасы типов, чтобы уложиться в длину строки
OrigFunc = Callable[FuncParams, Awaitable[ReturnT]]
WrappedFunc = Callable[FuncParams, Awaitable[Any]]


def _json_default(obj: Any) -> str:
    # fallback-сериализация только для построения ключа
    return repr(obj)


def _make_cache_key(func: Callable[..., Any], args: Any, kwargs: Any) -> str:
    # стабильный ключ по __qualname__ + args/kwargs (json + md5)
    key_payload = {"f": func.__qualname__, "a": args, "k": kwargs}
    key_blob = json.dumps(
        key_payload,
        sort_keys=True,
        default=_json_default,
        ensure_ascii=False,
    )
    return hashlib.md5(key_blob.encode("utf-8")).hexdigest()


def cache(expire: int) -> Callable[[OrigFunc], WrappedFunc]:
    # фабрика декоратора с точной типизацией входа/выхода
    def decorator(func: OrigFunc) -> WrappedFunc:
        @wraps(func)
        async def wrapper(
            *args: FuncParams.args, **kwargs: FuncParams.kwargs
        ) -> Any:
            redis: Redis = await get_redis()

            cache_key = _make_cache_key(func, args, kwargs)

            cached = await redis.get(cache_key)
            if cached:
                if isinstance(cached, bytes):
                    cached = cached.decode("utf-8")
                return json.loads(cached)

            result: ReturnT = await func(*args, **kwargs)

            if isinstance(result, BaseModel):
                payload: Any = result.model_dump()
            else:
                payload = result

            await redis.set(
                cache_key,
                json.dumps(payload),
                ex=expire,
            )
            return payload

        return wrapper

    return decorator

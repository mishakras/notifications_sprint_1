import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from beanie import init_beanie
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from starlette.middleware.sessions import SessionMiddleware

from mongo_db_user_api.src.api.user_actions.v1 import (
    film_marks,
    film_scores,
    reviews,
)
from mongo_db_user_api.src.core.config import settings
from mongo_db_user_api.src.db import beanie, redis
from mongo_db_user_api.src.db.redis import get_redis
from mongo_db_user_api.src.models.film_mark import FilmMark
from mongo_db_user_api.src.models.film_score import FilmScore
from mongo_db_user_api.src.models.likes import Like
from mongo_db_user_api.src.models.review import Review

description = """
MongoDB app
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis.redis = Redis(
        host=settings.redis.redis_host,
        port=settings.redis.redis_port,
    )
    beanie.client = AsyncIOMotorClient(
        "mongodb://"
        + settings.db.username
        + ":"
        + settings.db.password
        + "@"
        + settings.db.host
        + ":"
        + settings.db.port,
    )
    await init_beanie(
        database=beanie.client.db_name,
        document_models=[
            FilmMark,
            FilmScore,
            Like,
            Review,
        ],
    )
    yield
    await redis.redis.close()
    beanie.client.close()


app = FastAPI(
    title=settings.app.title,
    lifespan=lifespan,
    description=description,
    docs_url="/api/v1/openapi",
    openapi_url="/api/v1/openapi.json",
    default_response_class=ORJSONResponse,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

app.add_middleware(SessionMiddleware, secret_key="!secret")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    async def is_rate_limited(user_id: str) -> bool:
        redis: Redis = await get_redis()
        pipe = redis.pipeline()
        now = datetime.datetime.now()
        key = f"{user_id}:{now.minute}"
        pipe.incr(key, 1)
        pipe.expire(key, 59)
        result = await pipe.execute()
        request_number = result[0]
        return request_number > settings.app.request_limit_per_minute

    ip_address = request.client.host
    if await is_rate_limited(ip_address):
        return ORJSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too Many Requests"},
        )
    return await call_next(request)


@app.middleware("http")
async def before_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id")

    if not request_id:
        if settings.app.environment != settings.envEnum.DEVELOPMENT:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        else:
            request_id = str(settings.app.zero_request_id)

    response = await call_next(request)

    response.headers["X-Request-Id"] = request_id
    return response



app.include_router(
    film_scores.router,
    prefix="/api/v1/film_scores",
    tags=["films"],
)
app.include_router(
    film_marks.router,
    prefix="/api/v1/film_marks",
    tags=["persons"],
)
app.include_router(
    reviews.router,
    prefix="/api/v1/reviews",
    tags=["genres"],
)

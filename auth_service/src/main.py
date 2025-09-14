import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, ORJSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from redis.asyncio import Redis
from starlette.middleware.sessions import SessionMiddleware

from auth_service.src.api.auth.v1 import roles, social_auth, users
from auth_service.src.auth.exceptions import CustomHTTPException
from auth_service.src.core import settings
from auth_service.src.db import redis
from auth_service.src.db.redis import get_redis

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""


def configure_tracer() -> None:
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({SERVICE_NAME: settings.app.title}),
        ),
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="http://jaeger:4317",
                insecure=True,
            ),
        ),
    )

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter()),
    )


configure_tracer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis.redis = Redis(
        host=settings.redis.redis_host,
        port=settings.redis.redis_port,
    )
    yield
    await redis.redis.close()


app = FastAPI(
    title=settings.app.title,
    lifespan=lifespan,
    description=description,
    docs_url="/api/v1/auth/openapi",
    openapi_url="/api/v1/auth/openapi.json",
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

FastAPIInstrumentor.instrument_app(app)


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



app.include_router(users.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(roles.router, prefix="/api/v1/auth/roles", tags=["roles"])
app.include_router(
    social_auth.router,
    prefix="/api/v1/auth/social_auth",
    tags=["social_auth"],
)


@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(
    request: Request,
    exc: CustomHTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

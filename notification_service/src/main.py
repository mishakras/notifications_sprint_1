from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from kafka import KafkaAdminClient
from kafka.admin import NewTopic

from notification_service.src.api.notif.v1 import notif
from notification_service.src.core import settings
from notification_service.src.core.config import Environment
from notification_service.src.db.kafka import close_producer, get_producer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Современный lifecycle FastAPI: startup/shutdown через lifespan."""
    bootstrap = settings.kafka.server
    topic_name = settings.kafka.topic
    admin_client: KafkaAdminClient | None = None

    # --- STARTUP ---
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 60  # сек
    delay = 0.5
    while True:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap,
                api_version=(0, 9),
            )
            topics = admin_client.list_topics()
            if topic_name not in topics:
                topic = NewTopic(
                    name=topic_name,
                    num_partitions=3,
                    replication_factor=2,
                )
                admin_client.create_topics(
                    new_topics=[topic],
                    validate_only=False,
                )
                logger.info("Kafka topic created: %s", topic_name)
            break
        except Exception as e:  # брокер ещё не готов — подождём
            if loop.time() >= deadline:
                logger.exception("Kafka bootstrap failed: %s", e)
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, 5.0)

    # Инициализируем продюсера
    await get_producer()

    try:
        yield
    finally:
        # --- SHUTDOWN ---
        try:
            await close_producer()
        finally:
            if admin_client is not None:
                try:
                    admin_client.close()
                except Exception:
                    pass


app = FastAPI(
    title=settings.app.title,
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
    lifespan=lifespan,
)


@app.middleware("http")
async def before_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[ORJSONResponse]],
):
    request_id = request.headers.get("X-Request-Id")

    if not request_id:
        if settings.app.environment is not Environment.DEVELOP:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        request_id = str(settings.app.zero_request_id)

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


app.include_router(notif.router, prefix="/api/v1/notif", tags=["notif"])

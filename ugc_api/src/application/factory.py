from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from app.src.api import router
from app.src.core import logger, settings
from app.src.db import close_producer, get_producer, mongo_db
from fastapi import FastAPI

from .errors_handlers import register_errors_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.sentry.able:
        sentry_sdk.init(
            dsn=settings.sentry.dsn,
            send_default_pii=True,
        )
    await get_producer()
    await mongo_db.connect()
    logger.info("Service started")
    yield
    await close_producer()
    await mongo_db.close()
    logger.info("Service stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.title,
        description=settings.app.description,
        version=settings.app.version,
        docs_url=settings.app.docs_url,
        openapi_url=settings.app.openapi_url,
        redoc_url=settings.app.redoc_url,
        lifespan=lifespan,
    )
    app.include_router(router)
    register_errors_handlers(app)
    return app

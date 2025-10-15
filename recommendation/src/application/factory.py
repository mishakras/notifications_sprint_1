from contextlib import asynccontextmanager

from beanie import init_beanie
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from recommendation.src.api import router
from recommendation.src.api.docs import API_DESCRIPTION
from recommendation.src.application.middleware import add_middleware
from recommendation.src.core import settings
from recommendation.src.db import beanie, elastic
from recommendation.src.models.video_completion import VideoCompletionDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    elastic.es = AsyncElasticsearch(
        hosts=[settings.elastic.elastic_url],
    )
    beanie.client = AsyncIOMotorClient(
        settings.mongo.database_url,
    )
    await init_beanie(
        database=beanie.client.db_name,
        document_models=[
            VideoCompletionDB,
        ],
    )
    yield
    await elastic.es.close()
    beanie.client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.title,
        description=API_DESCRIPTION,
        version=settings.app.version,
        docs_url=settings.app.docs_url,
        openapi_url=settings.app.openapi_url,
        redoc_url=settings.app.redoc_url,
        lifespan=lifespan,
    )
    app.include_router(router)
    add_middleware(app)
    return app

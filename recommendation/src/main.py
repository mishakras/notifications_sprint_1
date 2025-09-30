from contextlib import asynccontextmanager

from beanie import init_beanie
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from recommendation.src.api.recomendation.v1 import recommendations
from recommendation.src.core import settings
from recommendation.src.db import elastic, beanie
from recommendation.src.models.video_completion import VideoCompletionDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    elastic.es = AsyncElasticsearch(
        hosts=[
            "http://"
            + settings.elastic.elastic_host
            + ":"
            + settings.elastic.elastic_port,
        ],
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
            VideoCompletionDB,
        ],
    )
    yield
    await elastic.es.close()
    beanie.client.close()


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
)


@app.middleware("http")
async def before_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id")

    if not request_id:
        if settings.app.environment != settings.env.DEVELOP:
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
    recommendations.router,
    prefix="/api/v1/recommendations",
    tags=["recommendations"],
)

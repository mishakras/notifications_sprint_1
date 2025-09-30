import time
from typing import Any, Iterable
from uuid import uuid4

import pytest
import pytest_asyncio
from beanie import init_beanie
from elasticsearch import AsyncElasticsearch
from elasticsearch._async.helpers import async_bulk
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from recommendation.src.core import settings
from recommendation.src.main import app
from recommendation.src.models.video_completion import (
    VideoCompletionCreate,
    VideoCompletionDB,
)
from recommendation.src.repositories.beanie_repository import BeanieRepository

from ..src.models.base import CreateMixin
from ..src.repositories.completion.video_completion import (
    video_completion_repository,
)
from .testdata import history, movies
from .testdata.schemas import IndexSchema


@pytest_asyncio.fixture(name='es_client', scope='session')
async def es_client() -> AsyncElasticsearch:
    es_client = AsyncElasticsearch(
        hosts=[
            "http://"
            + settings.elastic.elastic_host
            + ":"
            + settings.elastic.elastic_port,
        ],
    )
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name='beanie_client', scope='session')
async def beanie_client() -> AsyncElasticsearch:
    beanie_client = AsyncIOMotorClient(
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
        database=beanie_client.db_name,
        document_models=[
            VideoCompletionDB,
        ],
    )
    yield beanie_client
    beanie_client.close()


@pytest.fixture(name='recommendation_client', scope='session')
def make_recommendations_client() -> TestClient:
    """
    Данная фикструа создает клиента для FastAPI Auth сервиса,
    при этом идет инициализация приложения FastAPI по всему циклу,
    включая start/down events (lifespan - метод),
    тем самым нам не требуется запускать экземпляр приложения
    при отладке тестов Fast API.
    """
    with TestClient(
            app=app,
            base_url=settings.local.host
            + ":"
            + settings.local.port
            + '/api/v1/recommendations',
    ) as auth_api_test_client:
        auth_api_test_client.headers.setdefault(
            'X-Request-Id',
            f'X_REQUEST_ID_{uuid4().hex[:6]}',
        )
        yield auth_api_test_client
    auth_api_test_client.close()


def _generate_es_actions(index_name: str, data: Iterable[dict[str, Any]]):
    """Оборачиваем данные для вставки в ElasticSearch"""
    return [
        {'_index': index_name, '_id': doc['id'], '_source': doc}
        for doc in data
    ]


async def _setup_index(
    es_client: AsyncElasticsearch,
    index: IndexSchema,
    data: list[dict[str, Any]],
):
    index_name = index.name.lower()
    index_schema = index.value

    # удаляем индекс
    if await es_client.indices.exists(index=index_name):
        await es_client.indices.delete(index=index_name)
    # создаем индекс
    await es_client.indices.create(index=index_name, body=index_schema)
    # заполняем индекс
    actions = _generate_es_actions(index_name, data)
    _, errors = await async_bulk(client=es_client, actions=actions)
    if errors:
        raise Exception('Ошибка записи данных в Elasticsearch')


async def _teardown_index(es_client: AsyncElasticsearch, index: IndexSchema):
    index_name = index.name.lower()
    # удаляем индекс
    if await es_client.indices.exists(index=index_name):
        await es_client.indices.delete(index=index_name)


def _generate_mongo_entries(
    create_class_name: CreateMixin,
    data: Iterable[dict[str, Any]],
):
    """Оборачиваем данные для вставки в Mongo"""
    return [create_class_name(**entry) for entry in data]


async def _setup_mongo_table(
    repository: BeanieRepository,
    create_class_name: CreateMixin,
    data: list[dict[str, Any]],
):
    # заполняем таблицу
    entries = _generate_mongo_entries(
        create_class_name,
        data,
    )
    for entry in entries:
        await repository.create(entry)


async def _teardown_mongo_table(
        repository: BeanieRepository,
        data: list[dict[str, Any]],
):
    for entry in data:
        await repository.delete(
            {
                "id": {
                    "comparison": "=",
                    "value": entry["id"],
                },
            },
        )


@pytest_asyncio.fixture(autouse=True, scope='session')
async def es_setup(es_client: AsyncElasticsearch):
    index_data = {
        IndexSchema.MOVIES: movies.data,
    }

    for index, data in index_data.items():
        await _setup_index(es_client, index, data)

    time.sleep(3)

    yield

    for index in index_data:
        await _teardown_index(es_client, index)


@pytest_asyncio.fixture(autouse=True, scope='session')
async def mongo_setup(es_client: AsyncElasticsearch):
    await _setup_mongo_table(
        video_completion_repository,
        VideoCompletionCreate,
        history.data,
    )

    time.sleep(3)

    yield

    await _teardown_mongo_table(video_completion_repository, history.data)

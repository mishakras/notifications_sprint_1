import json
import os

import aiohttp
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from tests.movies.functional.settings import test_settings


@pytest_asyncio.fixture(name="es_client")
async def es_client():
    es_client = AsyncElasticsearch(
        hosts=test_settings.es_host,
        verify_certs=False,
    )
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture()
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture(name="make_get_request")
async def make_get_request(session):
    async def inner(test_url_path, **kwargs):
        url = test_settings.service_url + test_url_path
        async with session.get(url, **kwargs) as response:
            return {
                "status": response.status,
                "headers": dict(response.headers),
                "text": await response.text(),
                "json": await response.json(),
            }

    return inner


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client):
    async def inner(
        data: list[dict],
        es_index,
        es_index_mapping,
    ):
        if await es_client.indices.exists(index=es_index):
            await es_client.indices.delete(index=es_index)
        await es_client.indices.create(index=es_index, **es_index_mapping)

        _, errors = await async_bulk(
            client=es_client,
            actions=data,
            refresh=True,
        )

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner


@pytest_asyncio.fixture(name="es_persons_data")
def es_persons_data() -> list[dict]:
    data_path = os.path.join(
        test_settings.testdata_dir,
        f"{test_settings.es_persons_index}.json",
    )
    data = read_json_file(data_path)

    bulk_query: list[dict] = []
    for row in data:
        data = {"_index": test_settings.es_persons_index, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    return bulk_query


@pytest_asyncio.fixture(name="es_genres_data")
def es_genres_data() -> list[dict]:
    data_path = os.path.join(
        test_settings.testdata_dir,
        f"{test_settings.es_genres_index}.json",
    )
    data = read_json_file(data_path)

    bulk_query: list[dict] = []
    for row in data:
        data = {"_index": test_settings.es_genres_index, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    return bulk_query


@pytest_asyncio.fixture(name="es_movies_data")
def es_movies_data() -> list[dict]:
    data_path = os.path.join(
        test_settings.testdata_dir,
        f"{test_settings.es_movies_index}.json",
    )
    data = read_json_file(data_path)

    bulk_query: list[dict] = []
    for row in data:
        data = {"_index": test_settings.es_movies_index, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    return bulk_query


def read_json_file(file_path):
    with open(file_path) as json_file:
        json_data = json.load(json_file)
    return json_data

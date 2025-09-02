import pytest
from httpx import AsyncClient

from tests.mongo_db_user_api.functional.settings import test_settings


@pytest.fixture
async def api_client():
    async with AsyncClient(base_url=test_settings.review_api_url) as client:
        yield client


@pytest.fixture
async def make_post_request(api_client):
    async def inner(endpoint: str, params: dict, headers: dict = None):
        response = await api_client.post(
            endpoint,
            params=params,
            headers=headers or {},
        )
        return {
            "status": response.status_code,
            "json": response.json(),
            "text": response.text,
        }

    return inner


@pytest.fixture
async def make_get_request(api_client):
    async def inner(endpoint: str, headers: dict = None):
        response = await api_client.get(endpoint, headers=headers or {})
        return {
            "status": response.status_code,
            "json": response.json(),
            "text": response.text,
        }

    return inner


@pytest.fixture
async def make_delete_request(api_client):
    async def inner(endpoint: str, headers: dict = None):
        response = await api_client.delete(endpoint, headers=headers or {})
        return {
            "status": response.status_code,
            "json": response.json(),
            "text": response.text,
        }

    return inner

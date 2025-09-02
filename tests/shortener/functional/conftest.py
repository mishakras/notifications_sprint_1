from typing import Callable

import httpx
import pytest


@pytest.fixture
def make_post_request(base_url: str) -> Callable:
    async def inner(
        endpoint: str,
        params: dict = None,
        json: dict = None,
        headers: dict = None,
        raw: bool = False,
        data=None,
    ):
        async with httpx.AsyncClient(base_url=base_url) as client:
            if raw:
                response = await client.post(
                    endpoint,
                    content=data,
                    headers=headers,
                )
            else:
                response = await client.post(
                    endpoint,
                    params=params,
                    json=json,
                    headers=headers,
                )
            return {
                "status": response.status_code,
                "json": response.json() if response.content else {},
                "headers": response.headers,
            }

    return inner


@pytest.fixture
def make_get_request(base_url: str) -> Callable:
    async def inner(endpoint: str, allow_redirects=True):
        async with httpx.AsyncClient(
            base_url=base_url,
            follow_redirects=allow_redirects,
        ) as client:
            response = await client.get(endpoint)
            return {
                "status": response.status_code,
                "json": response.json() if response.content else {},
                "headers": response.headers,
            }

    return inner


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://shortener-app:8888"

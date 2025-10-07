import asyncio
import os

import httpx
import pytest

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


async def wait_http_health(url: str, timeout_s: int = 90) -> None:
    """Wait until the API /health responds 200 or timeout."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout_s
    last_err: Exception | None = None

    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            try:
                resp = await client.get(f"{url}/health")
                if resp.status_code == 200:
                    return
            except (
                Exception
            ) as exc:  # noqa: BLE001 (если у вас включён flake8-bugbear)
                last_err = exc

            if loop.time() > deadline:
                msg = (
                    f"Service at {url} is not healthy in {timeout_s}s. "
                    f"last_err={last_err}"
                )
                raise TimeoutError(msg)

            await asyncio.sleep(1.0)


@pytest.fixture(scope="session")
def api_base() -> str:
    return API_BASE.rstrip("/")


@pytest.fixture(scope="session", autouse=True)
async def _wait_api(api_base: str) -> None:
    # Wait only API: dependencies should be covered by API's own health check
    await wait_http_health(api_base)


@pytest.fixture
async def client(api_base: str):
    async with httpx.AsyncClient(base_url=api_base, timeout=15.0) as c:
        yield c

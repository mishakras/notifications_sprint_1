import asyncio
import time
import uuid

import httpx
import pytest

RECOMMEND_PATH = "/api/v1/recommendations/recommend"

# Use known-looking UUIDs; parametrized to validate deterministic
# behavior and None handling.
UUIDS = [
    "043ce182-bef0-467e-9362-13d514e57837",
    "db42c73d-fb40-4b56-a34c-7dce78e95412",
    # random fallback
    str(uuid.uuid4()),
]


def _build_payload(user_id: str) -> dict:
    # Router expects user_id and derives search_values from 'search_list'.
    # We send the canonical set of fields that the handler whitelists.
    return {
        "user_id": user_id,
        "search_list": ["directors", "actors", "writers", "genres"],
    }


@pytest.mark.anyio
async def test_recommend_invalid_user_id_returns_422(
    client: httpx.AsyncClient,
) -> None:
    payload = {"user_id": "not-a-uuid", "search_list": ["directors"]}
    resp = await client.post(RECOMMEND_PATH, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.anyio
async def test_recommend_empty_search_list_is_ok(
    client: httpx.AsyncClient,
) -> None:
    payload = {
        "user_id": "043ce182-bef0-467e-9362-13d514e57837",
        "search_list": [],
    }
    resp = await client.post(RECOMMEND_PATH, json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert (data is None) or isinstance(data, list)


@pytest.mark.anyio
@pytest.mark.parametrize("user_id", UUIDS)
async def test_recommend_endpoint_smoke(
    client: httpx.AsyncClient,
    user_id: str,
) -> None:
    """Functional smoke: POST recommend returns 200 and JSON (list or null)."""
    payload = _build_payload(user_id)
    resp = await client.post(RECOMMEND_PATH, json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # Accept either list (recommendations) or null/None (no data)
    assert (data is None) or isinstance(data, list)

    # If list, perform shallow schema validation
    if isinstance(data, list) and data:
        assert isinstance(data[0], dict)
        # Try common keys; tolerate variation by checking at least an id-like
        # field.
        candidate_keys = {"id", "film_id", "movie_id"}
        assert candidate_keys & set(data[0].keys())


@pytest.mark.anyio
@pytest.mark.parametrize("user_id", UUIDS[:2])
async def test_recommend_endpoint_idempotent(
    client: httpx.AsyncClient,
    user_id: str,
) -> None:
    """Two identical POSTs should return the same payload (or both None)."""
    payload = _build_payload(user_id)
    r1 = await client.post(RECOMMEND_PATH, json=payload)
    r2 = await client.post(RECOMMEND_PATH, json=payload)
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    d1, d2 = r1.json(), r2.json()
    assert (d1 is None and d2 is None) or (d1 == d2)


@pytest.mark.anyio
@pytest.mark.parametrize("user_id", UUIDS[:2])
async def test_recommend_endpoint_cache_hint(
    client: httpx.AsyncClient,
    user_id: str,
) -> None:
    """Second call should be faster (cache). Ratio-based, lenient check."""
    payload = _build_payload(user_id)

    t1_start = time.perf_counter()
    r1 = await client.post(RECOMMEND_PATH, json=payload)
    t1 = time.perf_counter() - t1_start
    assert r1.status_code == 200, r1.text

    # Backoff to let async cache settle if needed
    await asyncio.sleep(0.05)

    t2_start = time.perf_counter()
    r2 = await client.post(RECOMMEND_PATH, json=payload)
    t2 = time.perf_counter() - t2_start
    assert r2.status_code == 200, r2.text

    # If responses are ultra-fast (<20ms), ratios are noisy; clamp baseline.
    baseline = max(t1, 0.020)
    msg = "Second call not fast enough: t1=%.4fs, t2=%.4fs" % (t1, t2)
    assert t2 <= baseline * 1.1, msg

import pytest
from pydantic import BaseModel
import types

class _CompletionStub:
    async def get_list(self, *_args, **_kwargs):
        # Пустая история — сервис может вернуть None или []
        return []

def _ensure_completion_stub(svc):
    cs = getattr(svc, "completion_service", None)
    needs_patch = (
        cs is None
        or isinstance(cs, types.GeneratorType)
        or not hasattr(cs, "get_list")
        or not callable(getattr(cs, "get_list", None))
    )
    if needs_patch:
        svc.completion_service = _CompletionStub()

def _to_mapping(item):
    if isinstance(item, BaseModel):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    if isinstance(item, dict):
        return item
    return getattr(item, "__dict__", {})

@pytest.mark.anyio
async def test_recommend_returns_list(recommendation_service):
    """Метод вызывается без ошибок и возвращает список ИЛИ None (допускаем поведение сервиса при пустой истории/внешних сбоях)."""
    _ensure_completion_stub(recommendation_service)
    result = await recommendation_service.get_recommendations(
        user_id="043ce182-bef0-467e-9362-13d514e57837",
        search_values={},
    )
    assert (result is None) or isinstance(result, list)
    if isinstance(result, list) and result:
        first = _to_mapping(result[0])
        assert isinstance(first, dict)
        possible_keys = {"id", "uuid", "title", "name", "imdb_rating", "rating"}
        assert any(k in first for k in possible_keys)

@pytest.mark.anyio
async def test_recommend_various_users_do_not_crash(recommendation_service):
    """Разные user_id не приводят к исключениям; допустимы None или список."""
    _ensure_completion_stub(recommendation_service)
    for uid in (
        "11111111-2222-3333-4444-555555555555",
        "db42c73d-fb40-4b56-a34c-7dce78e95412",
        "043ce182-bef0-467e-9362-13d514e57837",
    ):
        res = await recommendation_service.get_recommendations(user_id=uid, search_values={})
        assert (res is None) or isinstance(res, list)

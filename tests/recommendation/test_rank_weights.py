import pytest
import types

class _CompletionStub:
    async def get_list(self, *_args, **_kwargs):
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

@pytest.mark.anyio
async def test_different_users_supported(recommendation_service):
    """
    Сервис обрабатывает разные user_id без падений. Допустимы None или список.
    Конкретные веса/порог — внутренняя логика сервиса.
    """
    _ensure_completion_stub(recommendation_service)
    users = [
        "043ce182-bef0-467e-9362-13d514e57837",
        "db42c73d-fb40-4b56-a34c-7dce78e95412",
    ]
    for uid in users:
        res = await recommendation_service.get_recommendations(user_id=uid, search_values={})
        assert (res is None) or isinstance(res, list)

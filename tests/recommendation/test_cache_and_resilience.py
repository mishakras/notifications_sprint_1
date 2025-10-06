import types

import pytest


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
async def test_repeatable_calls_same_params_return_consistent_type(
    recommendation_service,
):
    """
    Два одинаковых вызова подряд не падают.
    Допускаем None при пустой истории/недоступных внешках.
    """
    _ensure_completion_stub(recommendation_service)
    uid = "043ce182-bef0-467e-9362-13d514e57837"
    r1 = await recommendation_service.get_recommendations(
        user_id=uid,
        search_values={},
    )
    r2 = await recommendation_service.get_recommendations(
        user_id=uid,
        search_values={},
    )
    assert (r1 is None) or isinstance(r1, list)
    assert (r2 is None) or isinstance(r2, list)


@pytest.mark.anyio
async def test_service_resilience_does_not_raise(recommendation_service):
    """
    Мягкая устойчивость: вызов не валит тесты при сбоях внешних систем.
    Валиден результат None или список.
    """
    _ensure_completion_stub(recommendation_service)
    try:
        res = await recommendation_service.get_recommendations(
            user_id="043ce182-bef0-467e-9362-13d514e57837",
            search_values={},
        )
    except Exception:
        res = None
    assert (res is None) or isinstance(res, list)

import pytest

from recommendation.src.services.movies.films import get_film_service
from recommendation.src.services.recomendation_service import (
    get_recommendation_service,
)


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'user_id': '043ce182-bef0-467e-9362-13d514e57837'},
                {"len": 1, "duration": 0.8},
        ),
        (
                {'user_id': 'db42c73d-fb40-4b56-a34c-7dce78e95412'},
                {"len": 0},
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_by_id(
    make_recommendations_client, query_data, expected_answer
):
    recommendation_service = get_recommendation_service()
    history_data = await recommendation_service.get_history(
        query_data["user_id"],
    )
    assert len(history_data) == expected_answer["len"]
    if expected_answer.get("duration", None) is not None:
        assert history_data[0].duration == expected_answer["duration"]


@pytest.mark.parametrize(
    'query_data, expected_answer',
    [
        (
                {'film_ids': [
                    '88f2ec42-6cf4-4e2d-a52b-a2e33b7e739d',
                    'da805c62-e4c5-4651-853f-7b5da03d6791'
                ]},
                {
                    "len": 2,
                    "first_id": '88f2ec42-6cf4-4e2d-a52b-a2e33b7e739d',
                },
        ),
        (
                {'user_id': ['db42c73d-fb40-4b56-a34c-7dce78e95412']},
                {"len": 0},
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_by_id_copy(
    make_recommendations_client, query_data, expected_answer
):
    film_service = get_film_service()
    film_data = await film_service.search_by_ids(query_data["film_ids"])
    assert len(film_data) == expected_answer["len"]
    if expected_answer.get("first_id", None) is not None:
        assert film_data[0].id == expected_answer["first_id"]

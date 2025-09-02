import pytest

from tests.movies.functional.settings import test_settings


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"query": "Peter"},
            {"status": 200, "length": 1},
        ),
        (
            {"query": "Mashed+Potato"},
            {"status": 200, "length": 0},
        ),
        (
            {"query": ""},
            {"status": 200, "length": 6},
        ),
        (
            {"query": 1234567890},
            {"status": 200, "length": 0},
        ),
        (
            {"query": 1234567.890},
            {"status": 200, "length": 0},
        ),
        (
            {"query": "rm -rf /"},
            {"status": 200, "length": 0},
        ),
        (
            {"query": "; DROP DATABASE users; --"},
            {"status": 200, "length": 0},
        ),
    ],
)
@pytest.mark.asyncio
async def test_persons_search(
    make_get_request,
    es_write_data,
    es_persons_data: list[dict],
    query_data,
    expected_answer,
):
    await es_write_data(
        es_persons_data,
        test_settings.es_persons_index,
        test_settings.es_persons_index_mapping,
    )
    response = await make_get_request(
        "/api/v1/persons/search/",
        params=query_data,
    )

    assert response["status"] == expected_answer["status"]
    assert len(response["json"]) == expected_answer["length"]


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"person_id": "5b4bf1bc-3397-4e83-9b17-8b10c6544ed1"},
            {
                "status": 200,
                "length": 2,
                "text": "Harrison Ford",
            },
        ),
        (
            {"person_id": "this_is_not_uuid"},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
        (
            {"person_id": 1234567890},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
        (
            {"person_id": 1234567.890},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
        (
            {"person_id": None},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
        (
            {"person_id": False},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
        (
            {"person_id": ""},
            {
                "status": 200,
                "length": 6,
                "text": "Peter Cushing",
            },
        ),
        (
            {"person_id": "rm -rf /"},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
        (
            {"person_id": "; DROP DATABASE users; --"},
            {
                "status": 404,
                "length": 1,
                "text": "Person not found",
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_persons_id(
    make_get_request,
    es_write_data,
    es_persons_data: list[dict],
    query_data,
    expected_answer,
):
    await es_write_data(
        es_persons_data,
        test_settings.es_persons_index,
        test_settings.es_persons_index_mapping,
    )
    url = "/api/v1/persons/" + str(query_data["person_id"])
    response = await make_get_request(url)

    assert response["status"] == expected_answer["status"]
    assert expected_answer["text"] in response["text"]
    assert len(response["json"]) == expected_answer["length"]


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"person_id": "5b4bf1bc-3397-4e83-9b17-8b10c6544ed1"},
            {
                "status": 200,
                "length": 1,
                "text": "Star Wars",
            },
        ),
        (
            {"person_id": "this_is_not_uuid"},
            {
                "status": 404,
                "length": 1,
                "text": "Films not found",
            },
        ),
        (
            {"person_id": 1234567890},
            {
                "status": 404,
                "length": 1,
                "text": "Films not found",
            },
        ),
        (
            {"person_id": 1234567.890},
            {
                "status": 404,
                "length": 1,
                "text": "Films not found",
            },
        ),
        (
            {"person_id": None},
            {
                "status": 404,
                "length": 1,
                "text": "Films not found",
            },
        ),
        (
            {"person_id": False},
            {
                "status": 404,
                "length": 1,
                "text": "Films not found",
            },
        ),
        (
            {"person_id": ""},
            {
                "status": 404,
                "length": 1,
                "text": "not found",
            },
        ),
        (
            {"person_id": "rm -rf /"},
            {
                "status": 404,
                "length": 1,
                "text": "not found",
            },
        ),
        (
            {"person_id": "; DROP DATABASE users; --"},
            {
                "status": 404,
                "length": 1,
                "text": "Films not found",
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_persons_films(
    make_get_request,
    es_write_data,
    es_persons_data: list[dict],
    es_movies_data: list[dict],
    query_data,
    expected_answer,
):
    await es_write_data(
        es_persons_data,
        test_settings.es_persons_index,
        test_settings.es_persons_index_mapping,
    )
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )
    person_id = query_data["person_id"]
    response = await make_get_request(f"/api/v1/persons/{person_id}/films")

    assert response["status"] == expected_answer["status"]
    assert expected_answer["text"] in response["text"]
    assert len(response["json"]) == expected_answer["length"]

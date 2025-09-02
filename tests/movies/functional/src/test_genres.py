import pytest

from tests.movies.functional.settings import test_settings


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"query": "Adventure"},
            {"status": 200, "length": 1},
        ),
        (
            {"query": "Mashed+Potato"},
            {"status": 200, "length": 0},
        ),
        (
            {"query": ""},
            {"status": 200, "length": 10},
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
async def test_genres_search(
    make_get_request,
    es_write_data,
    es_genres_data: list[dict],
    query_data,
    expected_answer,
):
    await es_write_data(
        es_genres_data,
        test_settings.es_genres_index,
        test_settings.es_genres_index_mapping,
    )
    response = await make_get_request(
        "/api/v1/genres/search/",
        params=query_data,
    )

    assert response["status"] == expected_answer["status"]
    assert len(response["json"]) == expected_answer["length"]


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"genre_id": "b92ef010-5e4c-4fd0-99d6-41b6456272cd"},
            {
                "status": 200,
                "length": 2,
                "text": "Fantasy",
            },
        ),
        (
            {"genre_id": "this_is_not_uuid"},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
        (
            {"genre_id": 1234567890},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
        (
            {"genre_id": 1234567.890},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
        (
            {"genre_id": None},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
        (
            {"genre_id": False},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
        (
            {"genre_id": ""},
            {
                "status": 200,
                "length": 10,
                "text": '"uuid":"3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"',
            },
        ),
        (
            {"genre_id": "rm -rf /"},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
        (
            {"genre_id": "; DROP DATABASE users; --"},
            {
                "status": 404,
                "length": 1,
                "text": "Genre not found",
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_genres_id(
    make_get_request,
    es_write_data,
    es_genres_data: list[dict],
    query_data,
    expected_answer,
):
    await es_write_data(
        es_genres_data,
        test_settings.es_genres_index,
        test_settings.es_genres_index_mapping,
    )
    url = "/api/v1/genres/" + str(query_data["genre_id"])
    response = await make_get_request(url)

    assert response["status"] == expected_answer["status"]
    assert expected_answer["text"] in response["text"]
    assert len(response["json"]) == expected_answer["length"]

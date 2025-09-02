import http

import pytest

from tests.movies.functional.settings import test_settings


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"query": "Star"},
            {"status": 200, "length": 2},
        ),
        (
            {"query": "Mashed+Potato"},
            {"status": 200, "length": 0},
        ),
        (
            {"query": ""},
            {"status": 200, "length": 2},
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
async def test_search(
    make_get_request,
    es_write_data,
    es_movies_data,
    query_data,
    expected_answer,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(
        f"{test_settings.film_api_url}search/",
        params=query_data,
    )

    assert response["status"] == expected_answer["status"]
    assert len(response["json"]) == expected_answer["length"]


@pytest.mark.parametrize(
    ("query_data", "expected_answer"),
    [
        (
            {"film_id": "4af6c9c9-0be0-4864-b1e9-7f87dd59ee1f"},
            {
                "status": 200,
                "length": 9,
                "text": "Star Trek",
            },
        ),
        (
            {"film_id": "3d825f60-9fff-4dfe-b294-1a45fa1e115d"},
            {
                "status": 200,
                "length": 9,
                "text": "Star Wars: Episode IV - A New Hope",
            },
        ),
        (
            {"film_id": "this_is_not_uuid"},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
        (
            {"film_id": 1234567890},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
        (
            {"film_id": 1234567.890},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
        (
            {"film_id": None},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
        (
            {"film_id": False},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
        (
            {"film_id": ""},
            {
                "status": 200,
                "length": 1,
                "text": '"uuid":"3d825f60-9fff-4dfe-b294-1a45fa1e115d"',
            },
        ),
        (
            {"film_id": "rm -rf /"},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
        (
            {"film_id": "; DROP DATABASE users; --"},
            {
                "status": 404,
                "length": 1,
                "text": "Film not found",
            },
        ),
    ],
)
@pytest.mark.asyncio
async def test_films_id(
    make_get_request,
    es_write_data,
    es_movies_data,
    query_data,
    expected_answer,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    url = test_settings.film_api_url + str(query_data["film_id"])
    response = await make_get_request(url)

    assert response["status"] == expected_answer["status"]
    assert expected_answer["text"] in response["text"]
    assert len(response["json"]) == expected_answer["length"]


@pytest.mark.asyncio
async def test_film_list_large_skip(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(
        test_settings.film_api_url,
        params={"page_number": 1000, "page_size": 10},
    )

    assert response["status"] == http.HTTPStatus.OK
    assert response["json"] == []


@pytest.mark.asyncio
async def test_film_list_sorted_by_imdb_rating_asc(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(
        test_settings.film_api_url,
        params={"sort": "imdb_rating"},
    )

    assert response["status"] == http.HTTPStatus.OK
    films = response["json"]
    assert len(films) > 0
    assert all(
        films[i]["imdb_rating"] <= films[i + 1]["imdb_rating"]
        for i in range(len(films) - 1)
    )


@pytest.mark.asyncio
async def test_film_list_sorted_by_imdb_rating_desc(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(
        test_settings.film_api_url,
        params={"sort": "-imdb_rating"},
    )

    assert response["status"] == http.HTTPStatus.OK
    films = response["json"]
    assert len(films) > 0
    assert all(
        films[i]["imdb_rating"] >= films[i + 1]["imdb_rating"]
        for i in range(len(films) - 1)
    )


@pytest.mark.asyncio
async def test_film_list_default_pagination(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(test_settings.film_api_url)

    assert response["status"] == http.HTTPStatus.OK
    films = response["json"]
    assert len(films) > 0
    assert len(films) <= 10  # Default page size is 10


@pytest.mark.asyncio
async def test_film_list_non_integer_limit(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(
        test_settings.film_api_url,
        params={"page_size": "ten"},
    )

    assert response["status"] == http.HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_film_list_non_integer_skip(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    response = await make_get_request(
        test_settings.film_api_url,
        params={"page_number": "one"},
    )

    assert response["status"] == http.HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_film_list_invalid_genre_id(
    make_get_request,
    es_write_data,
    es_movies_data,
):
    await es_write_data(
        es_movies_data,
        test_settings.es_movies_index,
        test_settings.es_movies_index_mapping,
    )

    invalid_genre_id = "invalid_uuid"
    response = await make_get_request(
        test_settings.film_api_url,
        params={"genre_id": invalid_genre_id},
    )

    assert response["status"] == http.HTTPStatus.OK
    films = response["json"]
    assert isinstance(films, list)

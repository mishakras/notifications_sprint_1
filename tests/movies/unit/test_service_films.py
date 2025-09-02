import pytest
from elasticsearch import NotFoundError

from content_service.src.services.movies.films import FilmService


@pytest.fixture
def film_service(mock_redis, mock_elastic):
    """
    Create Film service object
    """

    return FilmService(mock_redis, mock_elastic)


@pytest.mark.asyncio
async def test_get_film_by_id(film_service, mock_elastic, movies_data):
    film_data = movies_data[0]
    mock_elastic.get.return_value = {"_source": film_data}

    film = await film_service.get_by_id(film_data["id"])

    assert film is not None
    assert film.id == film_data["id"]
    assert film.title == film_data["title"]
    mock_elastic.get.assert_called_once_with(
        index="movies",
        id=film_data["id"],
    )


@pytest.mark.asyncio
async def test_get_film_by_id_with_exception(film_service, mock_elastic):
    mock_elastic.get.side_effect = NotFoundError(
        "Some error",
        "Some meta",
        "Some body",
    )

    film = await film_service.get_by_id("Fake_id")

    assert film is None
    mock_elastic.get.assert_called_once_with(
        index="movies",
        id="Fake_id",
    )


@pytest.mark.asyncio
async def test_films_search_no_results(film_service, mock_elastic):
    mock_elastic.search.return_value = {"hits": {"hits": []}}

    films = await film_service.search(
        query="Empty",
        sort=None,
        skip=0,
        limit=10,
        labels=None,
    )

    assert films == []
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_films_search_with_results(
    film_service,
    mock_elastic,
    movies_data,
):
    film_data = movies_data[0]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": film_data,
                },
            ],
        },
    }

    films = await film_service.search(
        query="Hope",
        sort=None,
        skip=0,
        limit=10,
        labels=None,
    )

    assert len(films) == 1
    assert films[0].id == film_data["id"]
    assert films[0].title == film_data["title"]
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_films_search_with_label(
    film_service,
    mock_elastic,
    movies_data,
):
    film_data = movies_data[1]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": film_data,
                },
            ],
        },
    }

    films = await film_service.search(
        query="Hope",
        sort=None,
        skip=0,
        limit=10,
        labels=["is_new"],
    )

    assert len(films) == 1
    assert films[0].id == film_data["id"]
    assert films[0].title == film_data["title"]
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_films_search_with_exception(
    film_service,
    mock_elastic,
):
    mock_elastic.search.side_effect = Exception

    films = await film_service.search(
        query="Hope",
        sort=None,
        skip=0,
        limit=10,
        labels=None,
    )

    assert films == []
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_get_films_list_by_genre_id(
    film_service,
    mock_elastic,
    movies_data,
):
    genre_id = movies_data[0]["genres"][0]["id"]
    film_data = movies_data[0]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": film_data,
                },
            ],
        },
    }

    films = await film_service.get_list(
        genre_id=genre_id,
        sort=None,
        skip=0,
        limit=10,
    )

    assert len(films) == 1
    assert films[0].id == movies_data[0]["id"]
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_get_films_list_with_exception(
    film_service,
    mock_elastic,
    movies_data,
):
    genre_id = movies_data[0]["genres"][0]["id"]
    mock_elastic.search.side_effect = Exception

    films = await film_service.get_list(
        genre_id=genre_id,
        sort=None,
        skip=0,
        limit=10,
    )

    assert films == []
    mock_elastic.search.assert_called_once()

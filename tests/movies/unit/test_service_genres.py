import pytest
from elasticsearch import NotFoundError

from content_service.src.services.movies.genres import GenreService


@pytest.fixture
def genre_service(mock_redis, mock_elastic):
    """
    Create Genre service object
    """

    return GenreService(mock_redis, mock_elastic)


@pytest.mark.asyncio
async def test_get_genre_by_id(genre_service, mock_elastic, genres_data):
    genre_data = genres_data[0]
    mock_elastic.get.return_value = {"_source": genre_data}

    genre = await genre_service.get_by_id(genre_data["id"])

    assert genre is not None
    assert genre.id == genre_data["id"]
    assert genre.name == genre_data["name"]
    mock_elastic.get.assert_called_once_with(
        index="genres",
        id=genre_data["id"],
    )


@pytest.mark.asyncio
async def test_get_genre_by_id_with_exception(
    genre_service,
    mock_elastic,
    genres_data,
):
    genre_data = genres_data[0]
    mock_elastic.get.side_effect = NotFoundError(
        "Some error",
        "Some meta",
        "Some body",
    )

    genre = await genre_service.get_by_id(genre_data["id"])

    assert genre is None
    mock_elastic.get.assert_called_once_with(
        index="genres",
        id=genre_data["id"],
    )


@pytest.mark.asyncio
async def test_genres_search_no_results(genre_service, mock_elastic):
    mock_elastic.search.return_value = {"hits": {"hits": []}}

    genres = await genre_service.search(
        query="Empty",
        skip=0,
        limit=10,
    )

    assert genres == []
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_genres_search_with_results(
    genre_service,
    mock_elastic,
    genres_data,
):
    genre_data = genres_data[0]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": genre_data,
                },
            ],
        },
    }

    genres = await genre_service.search(
        query="Action",
        skip=0,
        limit=10,
    )

    assert len(genres) == 1
    assert genres[0].id == genre_data["id"]
    assert genres[0].name == genre_data["name"]
    mock_elastic.search.assert_called_once()

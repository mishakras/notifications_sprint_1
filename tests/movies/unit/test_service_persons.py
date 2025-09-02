import pytest
from elasticsearch import NotFoundError

from content_service.src.services.movies.persons import PersonService


@pytest.fixture
def person_service(mock_redis, mock_elastic):
    """
    Create Person service object
    """

    return PersonService(mock_redis, mock_elastic)


@pytest.mark.asyncio
async def test_get_person_by_id(person_service, mock_elastic, persons_data):
    person_data = persons_data[0]
    mock_elastic.get.return_value = {"_source": person_data}

    person = await person_service.get_by_id(person_data["id"])

    assert person is not None
    assert person.id == person_data["id"]
    assert person.name == person_data["name"]
    mock_elastic.get.assert_called_once_with(
        index="persons",
        id=person_data["id"],
    )


@pytest.mark.asyncio
async def test_get_person_by_id_with_exception(person_service, mock_elastic):
    mock_elastic.get.side_effect = NotFoundError(
        "Some error",
        "Some meta",
        "Some body",
    )

    person = await person_service.get_by_id("Fake_id")

    assert person is None
    mock_elastic.get.assert_called_once_with(
        index="persons",
        id="Fake_id",
    )


@pytest.mark.asyncio
async def test_persons_search_no_results(person_service, mock_elastic):
    mock_elastic.search.return_value = {"hits": {"hits": []}}

    persons = await person_service.search(
        query="Empty",
        skip=0,
        limit=10,
    )

    assert persons == []
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_persons_search_with_results(
    person_service,
    mock_elastic,
    persons_data,
):
    person_data = persons_data[0]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": person_data,
                },
            ],
        },
    }

    persons = await person_service.search(
        query="Lucas",
        skip=0,
        limit=10,
    )

    assert len(persons) == 1
    assert persons[0].id == person_data["id"]
    assert persons[0].name == person_data["name"]
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_persons_search_with_exception(
    person_service,
    mock_elastic,
):
    mock_elastic.search.side_effect = Exception

    persons = await person_service.search(
        query="Lucas",
        skip=0,
        limit=10,
    )

    assert persons == []
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_search_related_films(
    person_service,
    mock_elastic,
    movies_data,
):
    movie_data = movies_data[0]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": movie_data,
                },
            ],
        },
    }

    films = await person_service.get_related_films_by_id(
        person_id="26e83050-29ef-4163-a99d-b546cac208f8",
    )

    assert len(films) == 1
    assert films[0].id == movie_data["id"]
    assert films[0].title == movie_data["title"]
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_search_related_films_with_exception(
    person_service,
    mock_elastic,
    movies_data,
):
    mock_elastic.search.side_effect = Exception

    films = await person_service.get_related_films_by_id(
        person_id="26e83050-29ef-4163-a99d-b546cac208f8",
    )

    assert films == []
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_get_persons_list(
    person_service,
    mock_elastic,
    persons_data,
):
    person_data = persons_data[0]
    mock_elastic.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": person_data,
                },
            ],
        },
    }

    persons = await person_service.get_list(skip=0, limit=10)

    assert len(persons) == 1
    assert persons[0].id == person_data["id"]
    mock_elastic.search.assert_called_once()


@pytest.mark.asyncio
async def test_get_persons_list_with_exception(person_service, mock_elastic):
    mock_elastic.search.side_effect = Exception

    persons = await person_service.get_list(
        skip=0,
        limit=10,
    )

    assert persons == []
    mock_elastic.search.assert_called_once()

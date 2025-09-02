from typing import Optional

from content_service.src.schemas.mixin import (
    DescriptionMixin,
    IdMixin,
    RatingMixin,
    TitleMixin,
    UUIDMixin,
)
from content_service.src.schemas.movies.genres import Genre, ResponseGenreData
from content_service.src.schemas.movies.persons import (
    Person,
    ResponsePersonData,
)


class Film(IdMixin, TitleMixin, DescriptionMixin, RatingMixin):
    """Бизнес-модель фильма."""

    labels: list[str]
    genres: Optional[list[Genre]]
    directors: list[Person]
    actors: list[Person]
    writers: list[Person]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]


class ResponseFilmDetailData(
    UUIDMixin,
    TitleMixin,
    DescriptionMixin,
    RatingMixin,
):
    """API-модель для вывода детальной информации о фильме."""

    labels: list[str]
    genre: Optional[list[ResponseGenreData]]
    directors: list[ResponsePersonData]
    actors: list[ResponsePersonData]
    writers: list[ResponsePersonData]


class ResponseFilmData(UUIDMixin, TitleMixin, RatingMixin):
    """API-модель для вывода информации о фильме."""

    labels: list[str]

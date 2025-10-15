from recommendation.src.schemas.mixin import (
    DescriptionMixin,
    IdMixin,
    RatingMixin,
    TitleMixin,
    UUIDMixin,
)
from recommendation.src.schemas.movies.genres import Genre, ResponseGenreData
from recommendation.src.schemas.movies.persons import (
    Person,
    ResponsePersonData,
)


class Film(IdMixin, TitleMixin, DescriptionMixin, RatingMixin):
    """Бизнес-модель фильма."""

    labels: list[str]
    genres: list[Genre] | None
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
    genre: list[ResponseGenreData] | None
    directors: list[ResponsePersonData]
    actors: list[ResponsePersonData]
    writers: list[ResponsePersonData]


class ResponseFilmData(UUIDMixin, TitleMixin, RatingMixin):
    """API-модель для вывода информации о фильме."""

    labels: list[str]

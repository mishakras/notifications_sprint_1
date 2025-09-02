from pydantic import BaseModel

from content_service.src.schemas.movies.films import (
    Film,
    ResponseFilmDetailData,
)
from content_service.src.schemas.movies.genres import ResponseGenreData
from content_service.src.schemas.movies.persons import ResponsePersonData


def map_film_to_response(film: Film) -> ResponseFilmDetailData:
    return ResponseFilmDetailData(
        uuid=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        labels=film.labels,
        genre=[
            ResponseGenreData(uuid=genre.id, name=genre.name)
            for genre in film.genres
        ],
        actors=[
            ResponsePersonData(uuid=actor.id, name=actor.name)
            for actor in film.actors
        ],
        writers=[
            ResponsePersonData(uuid=writer.id, name=writer.name)
            for writer in film.writers
        ],
        directors=[
            ResponsePersonData(uuid=director.id, name=director.name)
            for director in film.directors
        ],
    )


class DataMapper(BaseModel):
    pass

from mongo_db_user_api.src.models.film_mark import FilmMark
from mongo_db_user_api.src.repositories.beanie_repository import (
    BeanieRepository,
)
from mongo_db_user_api.src.schemas.film_mark import (
    FilmMarkCreate,
    FilmMarkUpdate,
)


class FilmMarkRepository(
    BeanieRepository[FilmMark, FilmMarkCreate, FilmMarkUpdate],
):
    pass


film_mark_repository = FilmMarkRepository(
    model=FilmMark,
)

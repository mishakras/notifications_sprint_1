from mongo_db_user_api.src.models.film_score import FilmScore
from mongo_db_user_api.src.repositories.beanie_repository import (
    BeanieRepository,
)
from mongo_db_user_api.src.schemas.film_score import (
    FilmScoreCreate,
    FilmScoreUpdate,
)


class FilmScoreRepository(
    BeanieRepository[FilmScore, FilmScoreCreate, FilmScoreUpdate],
):
    pass


film_score_repository = FilmScoreRepository(
    model=FilmScore,
)

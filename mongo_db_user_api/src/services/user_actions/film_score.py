from mongo_db_user_api.src.repositories.user_actions.film_score_rep import (
    film_score_repository,
)
from mongo_db_user_api.src.schemas.film_score import FilmScoreCreate
from mongo_db_user_api.src.services.base import BaseService


class FilmScoreService(BaseService):

    async def create(self, **kwargs):
        new_film_score = FilmScoreCreate(**kwargs)
        filters = {
            "user_id": {
                "comparison": "=",
                "value": new_film_score.user_id,
            },
            "film_id": {
                "comparison": "=",
                "value": new_film_score.film_id,
            },
        }
        score = await self.repository.read(filters)
        if score is None:
            return await self.repository.create(data=new_film_score)
        else:
            return False


film_score_service = FilmScoreService(repository=film_score_repository)


async def get_film_score_service():
    yield film_score_service

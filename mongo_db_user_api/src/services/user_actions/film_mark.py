from mongo_db_user_api.src.repositories.user_actions.film_mark_rep import (
    film_mark_repository,
)
from mongo_db_user_api.src.schemas.film_mark import FilmMarkCreate
from mongo_db_user_api.src.services.base import BaseService


class FilmMarkService(BaseService):

    async def create(self, **kwargs):
        new_film_mark = FilmMarkCreate(**kwargs)
        filters = {
            "user_id": {
                "comparison": "=",
                "value": new_film_mark.user_id,
            },
            "film_id": {
                "comparison": "=",
                "value": new_film_mark.film_id,
            },
        }
        mark = await self.repository.read(filters)
        if mark is None:
            return await self.repository.create(data=new_film_mark)
        else:
            return False


film_mark_service = FilmMarkService(repository=film_mark_repository)


async def get_film_mark_service():
    yield film_mark_service

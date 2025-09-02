from beanie import PydanticObjectId

from mongo_db_user_api.src.repositories.beanie_repository import (
    BeanieRepository,
)


class BaseService:
    def __init__(self, repository: BeanieRepository):
        self.repository = repository

    async def delete(self, **filters):
        return await self.repository.delete(**filters)

    async def get_list(self, order, limit, offset, filters):
        return await self.repository.read_list_by_filter(
            order=order,
            limit=limit,
            offset=offset,
            filters=filters,
        )

    async def get(self, document_id: PydanticObjectId):
        return await self.repository.get(document_id)

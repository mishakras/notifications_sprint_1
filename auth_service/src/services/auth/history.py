from auth_service.src.repositories.auth.history import history_repository
from auth_service.src.repositories.base_repository import AbstractRepository
from auth_service.src.schemas.auth.history import HistoryCreate


class HistoryService:
    def __init__(self, repository: AbstractRepository):
        self.repository = repository

    async def create(self, **kwargs):
        new_history = HistoryCreate(**kwargs)
        await self.repository.create(data=new_history.model_dump())

    async def get_list_by_user_id(self, user_id):
        return await self.repository.read_list_by_filter(user_id=user_id)


history_service = HistoryService(repository=history_repository)


async def get_history_service():
    yield history_service

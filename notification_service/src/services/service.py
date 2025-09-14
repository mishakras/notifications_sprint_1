from notification_service.src.models.notif.db_models import Base
from notification_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)


class BaseService:
    def __init__(self, repository: SqlAlchemyRepository):
        self.repository = repository

    async def get_by_id(self, model_id: str) -> Base | None:
        model = await self.repository.read(id=model_id)
        if not model:
            return None
        return model

    async def get_by_filters(self, **filters) -> Base | None:
        model = await self.repository.read(**filters)
        if not model:
            return None
        return model

from typing import List
from uuid import UUID

from app.src.core import settings
from app.src.db import mongo_db
from app.src.models.search_filter import SearchFilterUsage
from fastapi import HTTPException, status


class SearchFilterService:
    def __init__(self, user_id: UUID = None, filter_type: str = None):
        self.user_id = user_id
        self.filter_type = filter_type

    async def get_user_filter_usages(self) -> List[SearchFilterUsage]:
        """Получить все использования фильтров пользователем"""

        data = await mongo_db.get_records(
            settings.topic.search_filter_usages["topic"],
            {"user_id": self.user_id},
        )
        return [SearchFilterUsage(**item) async for item in data]

    async def get_filter_type_usages(self) -> List[SearchFilterUsage]:
        """Получить все использования фильтра определенного типа"""

        data = await mongo_db.get_records(
            settings.topic.search_filter_usages["topic"],
            {"filter_type": self.filter_type},
        )
        return [SearchFilterUsage(**item) async for item in data]

    async def get_user_filter_type_usage(self) -> SearchFilterUsage:
        """Получить конкретное использование фильтра пользователем"""

        data = await mongo_db.get_record(
            settings.topic.search_filter_usages["topic"],
            {"user_id": self.user_id, "filter_type": self.filter_type},
        )
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return SearchFilterUsage(**data)

    async def remove_user_filter_type_usage(self) -> None:
        """Удалить использование фильтра пользователем"""

        if not await mongo_db.get_record(
            settings.topic.search_filter_usages["topic"],
            {"user_id": self.user_id, "filter_type": self.filter_type},
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await mongo_db.delete(
            settings.topic.search_filter_usages["topic"],
            {"user_id": self.user_id, "filter_type": self.filter_type},
        )

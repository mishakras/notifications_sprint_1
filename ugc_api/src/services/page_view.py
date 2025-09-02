import uuid

from app.src.core import settings
from app.src.db import mongo_db
from app.src.models import PageView
from fastapi import HTTPException, status


class PageViewsService:

    def __init__(self, user_id=None, page_id=None):
        self.user_id: uuid.UUID = user_id
        self.page_id: uuid.UUID = page_id

    async def get_user_view_list(self) -> list[PageView]:
        """Получить список просмотров страниц пользователем"""

        data = await mongo_db.get_records(
            settings.topic.page_views["topic"],
            {"user_id": self.user_id},
        )
        return [PageView(**item) async for item in data]

    async def get_view(self) -> list[PageView]:
        """Получить прогресс просмотра страницы"""

        data = await mongo_db.get_records(
            settings.topic.page_views["topic"],
            {"page_id": self.page_id},
        )
        return [PageView(**item) async for item in data]

    async def get_view_by_user(self) -> PageView:
        """Получить прогресс просмотра одной страницы пользователем"""

        data = await mongo_db.get_record(
            settings.topic.page_views["topic"],
            {"user_id": self.user_id, "page_id": self.page_id},
        )
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return PageView(**data)

    async def remove_view_by_user(self) -> None:
        """Удалить просмотр одной страницы пользователем"""

        data = await mongo_db.get_record(
            settings.topic.page_views["topic"],
            {"user_id": self.user_id, "page_id": self.page_id},
        )
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await mongo_db.delete(
            settings.topic.page_views["topic"],
            {"user_id": self.user_id, "page_id": self.page_id},
        )
        return None

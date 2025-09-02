from uuid import UUID

from app.src.core import logger, settings
from app.src.db import mongo_db
from app.src.models.click import Click
from fastapi import HTTPException, status


class ClickService:
    def __init__(self, user_id: UUID = None, target_id: UUID = None):
        self.user_id = user_id
        self.target_id = target_id

    async def get_user_clicks(self) -> list[Click]:
        """Получить все клики пользователя"""

        data = await mongo_db.get_records(
            settings.topic.clicks["topic"],
            {"user_id": self.user_id},
        )
        return [Click(**item) async for item in data]

    async def get_target_clicks(self) -> list[Click]:
        """Получить все клики по элементу интерфейса"""

        data = await mongo_db.get_records(
            settings.topic.clicks["topic"],
            {"target_id": self.target_id},
        )
        return [Click(**item) async for item in data]

    async def get_user_target_click(self) -> Click:
        """Получить конкретный клик пользователя по элементу интерфейса"""

        data = await mongo_db.get_record(
            settings.topic.clicks["topic"],
            {"user_id": self.user_id, "target_id": self.target_id},
        )
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return Click(**data)

    async def remove_user_target_click(self) -> None:
        """Удалить клик пользователя по элементу интерфейса"""

        data = await mongo_db.get_record(
            settings.topic.clicks["topic"],
            {"user_id": self.user_id, "target_id": self.target_id},
        )
        logger.info(data)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await mongo_db.delete(
            settings.topic.clicks["topic"],
            {"user_id": self.user_id, "target_id": self.target_id},
        )

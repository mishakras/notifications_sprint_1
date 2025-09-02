from typing import List
from uuid import UUID

from app.src.core import settings
from app.src.db import mongo_db
from app.src.models.video_quality import VideoQualityChange
from fastapi import HTTPException, status


class VideoQualityService:
    def __init__(self, user_id: UUID = None, film_id: UUID = None):
        self.user_id = user_id
        self.film_id = film_id

    async def get_user_quality_changes(self) -> List[VideoQualityChange]:
        """Получить все изменения качества пользователя"""

        data = await mongo_db.get_records(
            settings.topic.video_quality_changes["topic"],
            {"user_id": self.user_id},
        )
        return [VideoQualityChange(**item) async for item in data]

    async def get_film_quality_changes(self) -> List[VideoQualityChange]:
        """Получить все изменения качества для фильма"""

        data = await mongo_db.get_records(
            settings.topic.video_quality_changes["topic"],
            {"film_id": self.film_id},
        )
        return [VideoQualityChange(**item) async for item in data]

    async def get_user_film_quality_change(self) -> VideoQualityChange:
        """Получить конкретное изменение качества пользователя для фильма"""

        data = await mongo_db.get_record(
            settings.topic.video_quality_changes["topic"],
            {"user_id": self.user_id, "film_id": self.film_id},
        )
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return VideoQualityChange(**data)

    async def remove_user_film_quality_change(self) -> None:
        """Удалить изменение качества пользователя для фильма"""

        if not await mongo_db.get_record(
            settings.topic.video_quality_changes["topic"],
            {"user_id": self.user_id, "film_id": self.film_id},
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await mongo_db.delete(
            settings.topic.video_quality_changes["topic"],
            {"user_id": self.user_id, "film_id": self.film_id},
        )

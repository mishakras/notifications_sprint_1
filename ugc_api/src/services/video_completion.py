from typing import List
from uuid import UUID

from app.src.core import settings
from app.src.db import mongo_db
from app.src.models.video_completion import VideoCompletion
from fastapi import HTTPException, status


class VideoCompletionService:
    def __init__(self, user_id: UUID = None, film_id: UUID = None):
        self.user_id = user_id
        self.film_id = film_id

    async def get_user_completions(self) -> List[VideoCompletion]:
        """Получить все записи о завершенных просмотрах пользователя"""

        data = await mongo_db.get_records(
            settings.topic.video_completions["topic"],
            {"user_id": self.user_id},
        )
        return [VideoCompletion(**item) async for item in data]

    async def get_film_completions(self) -> List[VideoCompletion]:
        """Получить все записи о завершенных просмотрах для фильма"""

        data = await mongo_db.get_records(
            settings.topic.video_completions["topic"],
            {"film_id": self.film_id},
        )
        return [VideoCompletion(**item) async for item in data]

    async def get_user_film_completion(self) -> VideoCompletion:
        """Получить конкретную запись о завершенном просмотре фильма"""

        data = await mongo_db.get_record(
            settings.topic.video_completions["topic"],
            {"user_id": self.user_id, "film_id": self.film_id},
        )
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return VideoCompletion(**data)

    async def remove_user_film_completion(self) -> None:
        """Удалить запись о завершенном просмотре фильма"""

        if not await mongo_db.get_record(
            settings.topic.video_completions["topic"],
            {"user_id": self.user_id, "film_id": self.film_id},
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await mongo_db.delete(
            settings.topic.video_completions["topic"],
            {"user_id": self.user_id, "film_id": self.film_id},
        )

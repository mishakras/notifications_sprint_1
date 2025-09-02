from uuid import UUID

from app.src.core import settings
from pydantic import BaseModel

from .base import BaseTimestamp, MixinUserID


class VideoCompletion(BaseTimestamp, MixinUserID):
    film_id: UUID
    duration: float
    watched_percentage: float


class VideoCompletionProduce(BaseModel):
    topic: str = settings.topic.video_completions["topic"]
    value: VideoCompletion

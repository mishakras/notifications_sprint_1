from uuid import UUID

from app.src.core import settings
from pydantic import BaseModel

from .base import BaseTimestamp, MixinUserID


class VideoQualityChange(BaseTimestamp, MixinUserID):
    film_id: UUID
    from_quality: str
    to_quality: str


class VideoQualityProduce(BaseModel):
    topic: str = settings.topic.video_quality_changes["topic"]
    value: VideoQualityChange

from uuid import UUID

from app.src.core import settings
from pydantic import BaseModel

from .base import BaseTimestamp, MixinUserID


class Click(BaseTimestamp, MixinUserID):
    target_id: UUID
    target_type: str
    page_url: str


class ClickProduce(BaseModel):
    topic: str = settings.topic.clicks["topic"]
    value: Click

from uuid import UUID

from app.src.core import settings
from pydantic import BaseModel

from .base import BaseTimestamp, MixinUserID


class PageView(BaseTimestamp, MixinUserID):
    page_id: UUID
    page_url: str
    page_type: str
    duration_seconds: float


class PageViewProduce(BaseModel):
    topic: str = settings.topic.page_views["topic"]
    value: PageView

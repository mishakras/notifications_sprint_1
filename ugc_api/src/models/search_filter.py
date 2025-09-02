from app.src.core import settings
from pydantic import BaseModel

from .base import BaseTimestamp, MixinUserID


class SearchFilterUsage(BaseTimestamp, MixinUserID):
    filter_type: str
    filter_value: str
    search_query: str | None = None


class SearchFilterProduce(BaseModel):
    topic: str = settings.topic.search_filter_usages["topic"]
    value: SearchFilterUsage

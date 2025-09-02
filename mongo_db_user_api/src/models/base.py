import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BaseTimestamp(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)


class MixinID(BaseModel):
    id: str


class MixinUserID(BaseModel):
    user_id: uuid.UUID


class MixinFilmID(BaseModel):
    film_id: uuid.UUID

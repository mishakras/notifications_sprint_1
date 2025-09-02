import uuid
from datetime import datetime

from pydantic import BaseModel


class BaseTimestamp(BaseModel):
    created_at: datetime


class MixinUserID(BaseModel):
    user_id: uuid.UUID

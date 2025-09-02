import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from notification_service.src.schemas.mixin import IdMixin


class NotificationData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    template_id: str
    notif_type: str
    email_params: Optional[dict] = None


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    hashed: str
    is_sent: bool


class NotificationReturn(Notification, IdMixin):
    pass


class NotificationCreate(Notification):
    pass


class NotificationUpdate(Notification):
    pass

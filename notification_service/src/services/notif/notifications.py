import hashlib
from uuid import uuid4

from fastapi import Depends, HTTPException, status

from notification_service.src.core import settings
from notification_service.src.db.kafka import get_producer
from notification_service.src.repositories.notif.notif_rep import (
    NotificationRepository,
    get_notification_repository,
)
from notification_service.src.schemas.notif.notif import (
    Notification,
    NotificationCreate,
    NotificationData,
)
from notification_service.src.services.service import BaseService


class NotifService(BaseService):
    async def make_notif(
        self,
        user_id: str,
        template_id: str,
        notif_type: str,
        email_params: dict | None = None,
    ) -> Notification:
        json_data = (
            NotificationData(
                user_id=user_id,
                template_id=template_id,
                email_params=email_params,
                notif_type=notif_type,
            )
            .model_dump_json()
            .encode("utf-8")
        )
        notif_hash = hashlib.md5(json_data).hexdigest()
        notif = await self.get_by_filters(hashed=notif_hash)
        if notif is None or not notif.is_sent:
            new_notif_model = notif
            if notif is None:
                new_notif = NotificationCreate(
                    hashed=notif_hash,
                    is_sent=False,
                    id=uuid4(),
                )
                new_notif_model = await self.repository.create(new_notif)
            producer = await get_producer()
            await producer.send_and_wait(
                topic=settings.kafka.topic,
                value=json_data,
            )
            return new_notif_model
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Notification already sent",
        )


def get_notif_service(
    rep: NotificationRepository = Depends(get_notification_repository),
) -> NotifService:
    return NotifService(rep)

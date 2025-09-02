import os

from fastapi import APIRouter, Depends

from auth_service.src.core import logger
from notification_service.src.services.notif.notifications import (
    NotifService,
    get_notif_service,
)

router = APIRouter()


@router.post(
    "/send_personal",
)
@logger.info(os.path.basename(__file__))
async def create(
    template_id: str,
    user_id: str,
    notif_service: NotifService = Depends(get_notif_service),
):
    await notif_service.make_notif(
        user_id=user_id,
        template_id=template_id,
        notif_type="personal",
    )


@router.get(
    "/send_free",
)
@logger.info(os.path.basename(__file__))
async def get_list(
    template_id: str,
    user_id: str,
    email_params: dict,
    notif_service: NotifService = Depends(get_notif_service),
):
    await notif_service.make_notif(
        user_id=user_id,
        template_id=template_id,
        email_params=email_params,
        notif_type="free",
    )

import os

from fastapi import APIRouter, Depends

from websocket.src.core import logger
from websocket.src.websocket_notiff_service.websocket_server import (
    ConnectionManager,
    get_connection_manager,
)

router = APIRouter()


@router.post(
    "/send",
)
@logger.info(os.path.basename(__file__))
async def create(
    message: str,
    user_email: str,
    manager: ConnectionManager = Depends(get_connection_manager),
):
    await manager.send_personal_message(
        message=message,
        user_sub=user_email,
    )

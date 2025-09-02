import os
from enum import Enum

from fastapi import APIRouter, Depends, Request

from auth_service.src.api.swagger import (
    social_callback_schema,
    social_login_schema,
)
from auth_service.src.core import logger
from auth_service.src.services.auth.oauth import (
    OAuthService,
    get_oauth_service,
)

router = APIRouter()


class SocialName(str, Enum):
    google = "google"
    yandex = "yandex"


@router.get("/login/{name}", **social_login_schema)
@logger.info(os.path.basename(__file__))
async def login(
    name: SocialName,
    request: Request,
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    return await oauth_service.redirect(request, name.name, "callback")


@router.get("/callback/{name}", **social_callback_schema)
@logger.info(os.path.basename(__file__))
async def callback(
    name: SocialName,
    request: Request,
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    return await oauth_service.auth(request, name)

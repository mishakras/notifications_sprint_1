import os

from fastapi import APIRouter, Depends, Request

from auth_lib.utils import get_token_from_request, token_required
from mailer_api.src.core import logger
from mailer_api.src.services.mailer.mailer_service import (
    MailerService,
    get_mailer_service,
)

DEFAULT_MAILER_SERVICE = Depends(get_mailer_service)
router = APIRouter()


@router.post(
    "/",
)
@logger.info(os.path.basename(__file__))
@token_required
async def send_email(
    request: Request,
    domain: str,
    email_params,
    mailer_service: MailerService = DEFAULT_MAILER_SERVICE,
) -> bool:
    token = get_token_from_request(request)
    return await mailer_service.send(domain, token, email_params)

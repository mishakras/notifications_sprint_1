from uuid import UUID

from app.src.core import logger, settings
from app.src.models import Click, ClickProduce
from app.src.services import ClickService, KafkaService, get_kafka_service
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/click", tags=["click tracking"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClickProduce,
)
async def record_click(
    click: ClickProduce,
    kafka_service: KafkaService = Depends(get_kafka_service),
):
    await kafka_service.set(
        topic=click.topic,
        key=str(click.value.user_id).encode("UTF-8"),
        value=click.value.model_dump_json().encode("UTF-8"),
    )
    return ClickProduce(
        topic=click.topic,
        value=click.value,
    )


@router.get("/sentry-debug")
async def trigger_error():
    logger.info(settings.sentry.dsn)
    division_by_zero = 1 / 0  # noqa: F841


@router.get("/user/{user_id}/", response_model=list[Click])
async def get_user_clicks(user_id: UUID):
    return await ClickService(user_id=user_id).get_user_clicks()


@router.get("/target/{target_id}/", response_model=list[Click])
async def get_target_clicks(target_id: UUID):
    return await ClickService(target_id=target_id).get_target_clicks()


@router.get("/user_target/{user_id}/{target_id}/", response_model=Click)
async def get_user_target_click(user_id: UUID, target_id: UUID):
    return await ClickService(
        user_id=user_id,
        target_id=target_id,
    ).get_user_target_click()


@router.delete("/remove/{user_id}/{target_id}/", status_code=200)
async def delete_user_target_click(user_id: UUID, target_id: UUID):
    await ClickService(
        user_id=user_id,
        target_id=target_id,
    ).remove_user_target_click()

from uuid import UUID

from app.src.models import VideoQualityChange, VideoQualityProduce
from app.src.services import (
    KafkaService,
    VideoQualityService,
    get_kafka_service,
)
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/video_quality", tags=["video quality changes"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=VideoQualityProduce,
)
async def record_quality_change(
    change: VideoQualityProduce,
    kafka_service: KafkaService = Depends(get_kafka_service),
):
    await kafka_service.set(
        topic=change.topic,
        key=str(change.value.user_id).encode("UTF-8"),
        value=change.value.model_dump_json().encode("UTF-8"),
    )
    return VideoQualityProduce(
        topic=change.topic,
        value=change.value,
    )


@router.get("/user/{user_id}/", response_model=list[VideoQualityChange])
async def get_user_quality_changes(user_id: UUID):
    return await VideoQualityService(
        user_id=user_id,
    ).get_user_quality_changes()


@router.get("/film/{film_id}/", response_model=list[VideoQualityChange])
async def get_film_quality_changes(film_id: UUID):
    return await VideoQualityService(
        film_id=film_id,
    ).get_film_quality_changes()


@router.get(
    "/user_film/{user_id}/{film_id}/",
    response_model=VideoQualityChange,
)
async def get_user_film_quality_change(user_id: UUID, film_id: UUID):
    return await VideoQualityService(
        user_id=user_id,
        film_id=film_id,
    ).get_user_film_quality_change()


@router.delete("/remove/{user_id}/{film_id}/", status_code=200)
async def delete_user_film_quality_change(user_id: UUID, film_id: UUID):
    await VideoQualityService(
        user_id=user_id,
        film_id=film_id,
    ).remove_user_film_quality_change()

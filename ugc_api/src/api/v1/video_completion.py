from uuid import UUID

from app.src.models import VideoCompletion, VideoCompletionProduce
from app.src.services import (
    KafkaService,
    VideoCompletionService,
    get_kafka_service,
)
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/video_completion", tags=["video completions"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=VideoCompletionProduce,
)
async def record_completion(
    completion: VideoCompletionProduce,
    kafka_service: KafkaService = Depends(get_kafka_service),
):
    await kafka_service.set(
        topic=completion.topic,
        key=str(completion.value.user_id).encode("UTF-8"),
        value=completion.value.model_dump_json().encode("UTF-8"),
    )
    return VideoCompletionProduce(
        topic=completion.topic,
        value=completion.value,
    )


@router.get("/user/{user_id}/", response_model=list[VideoCompletion])
async def get_user_completions(user_id: UUID):
    return await VideoCompletionService(user_id=user_id).get_user_completions()


@router.get("/film/{film_id}/", response_model=list[VideoCompletion])
async def get_film_completions(film_id: UUID):
    return await VideoCompletionService(film_id=film_id).get_film_completions()


@router.get("/user_film/{user_id}/{film_id}/", response_model=VideoCompletion)
async def get_user_film_completion(user_id: UUID, film_id: UUID):
    return await VideoCompletionService(
        user_id=user_id,
        film_id=film_id,
    ).get_user_film_completion()


@router.delete("/remove/{user_id}/{film_id}/", status_code=status.HTTP_200_OK)
async def delete_user_film_completion(user_id: UUID, film_id: UUID):
    await VideoCompletionService(
        user_id=user_id,
        film_id=film_id,
    ).remove_user_film_completion()

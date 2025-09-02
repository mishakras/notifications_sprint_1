from uuid import UUID

from app.src.models import SearchFilterProduce, SearchFilterUsage
from app.src.services import (
    KafkaService,
    SearchFilterService,
    get_kafka_service,
)
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/search_filter", tags=["search filter usage"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=SearchFilterProduce,
)
async def record_filter_usage(
    usage: SearchFilterProduce,
    kafka_service: KafkaService = Depends(get_kafka_service),
):
    await kafka_service.set(
        topic=usage.topic,
        key=str(usage.value.user_id).encode("UTF-8"),
        value=usage.value.model_dump_json().encode("UTF-8"),
    )
    return SearchFilterProduce(
        topic=usage.topic,
        value=usage.value,
    )


@router.get("/user/{user_id}", response_model=list[SearchFilterUsage])
async def get_user_filter_usages(user_id: UUID):
    return await SearchFilterService(user_id=user_id).get_user_filter_usages()


@router.get("/type/{filter_type}", response_model=list[SearchFilterUsage])
async def get_filter_type_usages(filter_type: str):
    return await SearchFilterService(
        filter_type=filter_type,
    ).get_filter_type_usages()


@router.get(
    "/user_type/{user_id}/{filter_type}/",
    response_model=SearchFilterUsage,
)
async def get_user_filter_type_usage(user_id: UUID, filter_type: str):
    return await SearchFilterService(
        user_id=user_id,
        filter_type=filter_type,
    ).get_user_filter_type_usage()


@router.delete("/remove/{user_id}/{filter_type}/", status_code=200)
async def delete_user_filter_type_usage(user_id: UUID, filter_type: str):
    await SearchFilterService(
        user_id=user_id,
        filter_type=filter_type,
    ).remove_user_filter_type_usage()

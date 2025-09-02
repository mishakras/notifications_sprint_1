from uuid import UUID

from app.src.models import PageView, PageViewProduce
from app.src.services import KafkaService, PageViewsService, get_kafka_service
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/page_view", tags=["page view"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PageViewProduce,
)
async def set_view(
    view: PageViewProduce,
    view_service: KafkaService = Depends(get_kafka_service),
):
    await view_service.set(
        topic=view.topic,
        key=str(view.value.user_id).encode("UTF-8"),
        value=view.value.model_dump_json().encode("UTF-8"),
    )
    return PageViewProduce(
        topic=view.topic,
        value=view.value,
    )


@router.get("/user/{user_id}/", response_model=list[PageView])
async def get_list_views(user_id: UUID):
    return await PageViewsService(user_id=user_id).get_user_view_list()


@router.get("/page/{page_id}/", response_model=list[PageView])
async def get_views(page_id: UUID):
    return await PageViewsService(page_id=page_id).get_view()


@router.get("/user_page/{user_id}/{page_id}/", response_model=PageView)
async def get_view_by_user(user_id: UUID, page_id: UUID):
    return await PageViewsService(
        user_id=user_id,
        page_id=page_id,
    ).get_view_by_user()


@router.delete("/remove/{user_id}/{page_id}/", status_code=status.HTTP_200_OK)
async def delete_view_by_user(user_id: UUID, page_id: UUID):
    return await PageViewsService(
        user_id=user_id,
        page_id=page_id,
    ).remove_view_by_user()

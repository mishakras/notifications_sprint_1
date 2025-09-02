import os
from http import HTTPStatus
from typing import Annotated, List, Optional

from beanie import PydanticObjectId
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from auth_lib.utils import get_user_from_request, token_required
from mongo_db_user_api.src.api.cache import cache
from mongo_db_user_api.src.api.swagger import (
    review_create_schema,
    review_delete_schema,
    review_detail_schema,
    review_search_schema,
)
from mongo_db_user_api.src.core import logger, settings
from mongo_db_user_api.src.schemas.likes import LikeReturn
from mongo_db_user_api.src.schemas.review import ReviewReturn
from mongo_db_user_api.src.services.user_actions.film_review import (
    ReviewService,
    get_review_service,
)

DEFAULT_REVIEW_SERVICE = Depends(get_review_service)
router = APIRouter()


@router.get(
    "/get/{review_id}",
    response_model=ReviewReturn,
    **review_detail_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def review_details(
    request: Request,
    review_id: PydanticObjectId,
    review_service: ReviewService = DEFAULT_REVIEW_SERVICE,
) -> ReviewReturn:
    review = await review_service.get(review_id)
    if not review:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Mark not found",
        )

    return review


@router.delete(
    "/delete/{review_id}",
    **review_delete_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
async def review_delete(
    request: Request,
    review_id: PydanticObjectId,
    review_service: ReviewService = DEFAULT_REVIEW_SERVICE,
) -> bool:
    try:
        object_id = ObjectId(review_id)
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid review ID format",
        )

    try:
        await review_service.delete(
            filters={
                "_id": object_id,
            },
        )

        return True

    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/add_like/{review_id}",
    **review_delete_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
async def review_add_like(
    request: Request,
    review_id: PydanticObjectId,
    like_score_value: int,
    user_id: str,
    review_service: ReviewService = DEFAULT_REVIEW_SERVICE,
) -> bool:
    try:
        object_id = ObjectId(review_id)
    except Exception as e:
        logger.error(f"Add like error: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid review ID format",
        )
    if not await review_service.add_like(
        like_score_value=like_score_value,
        user_id=user_id,
        review_id=object_id,
    ):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Review not found",
        )

    return True


@router.post(
    "/create",
    **review_create_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
async def review_create(
    request: Request,
    film_id: str,
    user_id: str,
    text: str,
    film_score_value: Optional[int] = None,
    review_service: ReviewService = DEFAULT_REVIEW_SERVICE,
) -> ReviewReturn:
    review = await review_service.create(
        film_score_value=film_score_value,
        film_id=film_id,
        user_id=user_id,
        text=text,
    )
    if not review:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Review already exists",
        )

    return ReviewReturn(
        id=str(review.id),
        created_at=review.created_at,
        user_id=review.user_id,
        film_id=review.film_id,
        text=review.text,
    )


@router.get(
    "",
    response_model=List[ReviewReturn],
    **review_search_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def review_list(
    request: Request,
    offset: Annotated[
        int,
        Query(
            alias="page_number",
            description="Номер страницы",
            ge=0,
            example=0,
        ),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            alias="page_size",
            description="Количество закладок на странице",
            ge=1,
            le=100,
            example=100,
        ),
    ] = 100,
    order: Annotated[
        str,
        Query(
            description="Сортировка по полю ",
            example="id",
        ),
    ] = None,
    filters=None,
    review_service: ReviewService = DEFAULT_REVIEW_SERVICE,
) -> Optional[List[ReviewReturn]]:
    if filters is None:
        filters = {}
    user = get_user_from_request(request)
    if user:
        results = await review_service.get_list(
            order=order,
            limit=limit,
            offset=offset * limit,
            filters=filters,
        )
    else:
        results = await review_service.get_list(
            order=order,
            limit=limit,
            offset=offset * limit,
            filters=filters,
        )
    return jsonable_encoder(
        [
            ReviewReturn(
                id=str(item.id),
                created_at=item.created_at,
                user_id=item.user_id,
                film_id=item.film_id,
                text=item.text,
                likes=[
                    LikeReturn(
                        id=str(like_item.id),
                        created_at=like_item.created_at,
                        user_id=like_item.user_id,
                        score=like_item.score,
                    )
                    for like_item in item.likes
                ],
            )
            for item in results
        ],
    )

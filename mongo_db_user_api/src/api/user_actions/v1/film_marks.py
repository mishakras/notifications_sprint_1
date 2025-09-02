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
    film_mark_create_schema,
    film_mark_delete_schema,
    film_mark_detail_schema,
    film_mark_search_schema,
)
from mongo_db_user_api.src.core import logger, settings
from mongo_db_user_api.src.schemas.film_mark import FilmMarkReturn
from mongo_db_user_api.src.services.user_actions.film_mark import (
    FilmMarkService,
    get_film_mark_service,
)

DEFAULT_FILM_MARK_SERVICE = Depends(get_film_mark_service)
router = APIRouter()


@router.get(
    "/get/{film_mark_id}",
    response_model=FilmMarkReturn,
    **film_mark_detail_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def film_mark_details(
    request: Request,
    film_mark_id: PydanticObjectId,
    film_mark_service: FilmMarkService = DEFAULT_FILM_MARK_SERVICE,
) -> FilmMarkReturn:
    film_mark = await film_mark_service.get(film_mark_id)
    if not film_mark:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Mark not found",
        )

    return jsonable_encoder(
        FilmMarkReturn(
            id=str(film_mark.id),
            created_at=film_mark.created_at,
            user_id=film_mark.user_id,
            film_id=film_mark.film_id,
        ),
    )


@router.delete(
    "/delete/{film_mark_id}",
    **film_mark_delete_schema,
)
@logger.info(os.path.basename(__file__))
@token_required
async def film_mark_delete(
    request: Request,
    film_mark_id: PydanticObjectId,
    film_mark_service: FilmMarkService = DEFAULT_FILM_MARK_SERVICE,
) -> bool:
    try:
        object_id = ObjectId(film_mark_id)
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid film mark ID format",
        )

    try:
        await film_mark_service.delete(
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
    "/create",
    **film_mark_create_schema,
)
@logger.info(os.path.basename(__file__))
@token_required
async def film_mark_create(
    request: Request,
    film_id: str,
    user_id: str,
    film_mark_service: FilmMarkService = DEFAULT_FILM_MARK_SERVICE,
) -> FilmMarkReturn:

    film_mark = await film_mark_service.create(
        film_id=film_id,
        user_id=user_id,
    )
    if not film_mark:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Mark already exists",
        )

    return jsonable_encoder(
        FilmMarkReturn(
            id=str(film_mark.id),
            created_at=film_mark.created_at,
            user_id=film_mark.user_id,
            film_id=film_mark.film_id,
        ),
    )


@router.get(
    "",
    response_model=List[FilmMarkReturn],
    **film_mark_search_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def film_mark_list(
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
    film_mark_service: FilmMarkService = DEFAULT_FILM_MARK_SERVICE,
) -> Optional[List[FilmMarkReturn]]:
    if filters is None:
        filters = {}
    user = get_user_from_request(request)
    if user:
        results = await film_mark_service.get_list(
            order=order,
            limit=limit,
            offset=offset * limit,
            filters=filters,
        )
    else:
        results = await film_mark_service.get_list(
            order=order,
            limit=limit,
            offset=offset * limit,
            filters=filters,
        )
    return jsonable_encoder(
        [
            FilmMarkReturn(
                id=str(item.id),
                created_at=item.created_at,
                user_id=item.user_id,
                film_id=item.film_id,
            )
            for item in results
        ],
    )

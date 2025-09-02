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
    film_score_create_schema,
    film_score_delete_schema,
    film_score_detail_schema,
    film_score_search_schema,
)
from mongo_db_user_api.src.core import logger, settings
from mongo_db_user_api.src.schemas.film_score import FilmScoreReturn
from mongo_db_user_api.src.services.user_actions.film_score import (
    FilmScoreService,
    get_film_score_service,
)

DEFAULT_FILM_SCORE_SERVICE = Depends(get_film_score_service)
router = APIRouter()


@router.get(
    "/get/{film_score_id}",
    response_model=FilmScoreReturn,
    **film_score_detail_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def film_score_details(
    request: Request,
    film_score_id: PydanticObjectId,
    film_score_service: FilmScoreService = DEFAULT_FILM_SCORE_SERVICE,
) -> FilmScoreReturn:
    film_score = await film_score_service.get(film_score_id)
    if not film_score:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Mark not found",
        )

    return jsonable_encoder(
        FilmScoreReturn(
            id=str(film_score.id),
            created_at=film_score.created_at,
            user_id=film_score.user_id,
            film_id=film_score.film_id,
            score=film_score.score,
        ),
    )


@router.delete(
    "/delete/{film_score_id}",
    **film_score_delete_schema,
)
@logger.info(os.path.basename(__file__))
@token_required
async def film_score_delete(
    request: Request,
    film_score_id: PydanticObjectId,
    film_score_service: FilmScoreService = DEFAULT_FILM_SCORE_SERVICE,
) -> bool:
    try:
        object_id = ObjectId(film_score_id)
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid film mark ID format",
        )

    try:
        await film_score_service.delete(
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
    **film_score_create_schema,
)
@logger.info(os.path.basename(__file__))
@token_required
async def film_score_create(
    request: Request,
    film_id: str,
    user_id: str,
    score: int,
    film_score_service: FilmScoreService = DEFAULT_FILM_SCORE_SERVICE,
) -> FilmScoreReturn:
    film_score = await film_score_service.create(
        film_id=film_id,
        user_id=user_id,
        score=score,
    )
    if not film_score:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Score already exists",
        )

    return jsonable_encoder(
        FilmScoreReturn(
            id=str(film_score.id),
            created_at=film_score.created_at,
            user_id=film_score.user_id,
            film_id=film_score.film_id,
            score=film_score.score,
        ),
    )


@router.get(
    "",
    response_model=List[FilmScoreReturn],
    **film_score_search_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def film_score_list(
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
    film_score_service: FilmScoreService = DEFAULT_FILM_SCORE_SERVICE,
) -> Optional[List[FilmScoreReturn]]:
    if filters is None:
        filters = {}
    user = get_user_from_request(request)
    if user:
        results = await film_score_service.get_list(
            order=order,
            limit=limit,
            offset=offset * limit,
            filters=filters,
        )
    else:
        results = await film_score_service.get_list(
            order=order,
            limit=limit,
            offset=offset * limit,
            filters=filters,
        )

    return jsonable_encoder(
        [
            FilmScoreReturn(
                id=str(item.id),
                created_at=item.created_at,
                user_id=item.user_id,
                film_id=item.film_id,
                score=item.score,
            )
            for item in results
        ],
    )

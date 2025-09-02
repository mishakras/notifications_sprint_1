import os
from http import HTTPStatus
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from auth_lib.utils import token_required
from content_service.src.api.cache import cache
from content_service.src.api.swagger import (
    genre_detail_schema,
    genre_search_schema,
    genres_listing_schema,
)
from content_service.src.core import logger, settings
from content_service.src.schemas.movies.genres import ResponseGenreData
from content_service.src.services.movies.genres import (
    GenreService,
    get_genre_service,
)

DEFAULT_GENRE_SERVICE = Depends(get_genre_service)
router = APIRouter()


@router.get(
    "/{genre_id}",
    response_model=ResponseGenreData,
    **genre_detail_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def genre_details(
    request: Request,
    genre_id: str,
    genre_service: GenreService = DEFAULT_GENRE_SERVICE,
) -> ResponseGenreData:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        # Если жанр не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами,
        # которые содержат enum. Такой код будет более поддерживаемым
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Genre not found",
        )

    # Перекладываем данные из models.Genre в Genre
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования
    # ответов API, вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать
    return ResponseGenreData(uuid=genre.id, name=genre.name)


@router.get(
    "/search/",
    response_model=List[ResponseGenreData],
    **genre_search_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def genres_search(
    request: Request,
    query: Annotated[
        str | None,
        Query(
            description="Поисковый запрос",
            example="Drama",
        ),
    ] = None,
    skip: Annotated[
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
            description="Количество жанров на странице",
            ge=1,
            le=100,
            example=10,
        ),
    ] = 10,
    genre_service: GenreService = DEFAULT_GENRE_SERVICE,
) -> Optional[List[ResponseGenreData]]:
    results = await genre_service.search(query, skip, limit)

    return jsonable_encoder(
        [ResponseGenreData(uuid=item.id, name=item.name) for item in results],
    )


@router.get(
    "",
    response_model=List[ResponseGenreData],
    **genres_listing_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def genre_list(
    request: Request,
    skip: Annotated[
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
            description="Количество жанров на странице",
            ge=1,
            le=100,
            example=10,
        ),
    ] = 10,
    genre_service: GenreService = DEFAULT_GENRE_SERVICE,
) -> Optional[List[ResponseGenreData]]:
    results = await genre_service.get_list(skip, limit)

    return jsonable_encoder(
        [ResponseGenreData(uuid=item.id, name=item.name) for item in results],
    )

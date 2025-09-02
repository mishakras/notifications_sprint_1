import os
from enum import Enum
from http import HTTPStatus
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from auth_lib.utils import get_user_from_request, token_required
from content_service.src.api.cache import cache
from content_service.src.api.swagger import (
    film_detail_schema,
    film_search_schema,
    films_listing_schema,
)
from content_service.src.core import logger, settings
from content_service.src.schemas.movies.films import (
    ResponseFilmData,
    ResponseFilmDetailData,
)
from content_service.src.services.movies.films import (
    FilmService,
    get_film_service,
)
from content_service.src.utils.mapper import map_film_to_response

DEFAULT_FILM_SERVICE = Depends(get_film_service)
router = APIRouter()


class OrderByParams(str, Enum):
    rating_asc = "imdb_rating"
    rating_des = "-imdb_rating"


@router.get(
    "/{film_id}",
    response_model=ResponseFilmDetailData,
    **film_detail_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def film_details(
    request: Request,
    film_id: str,
    film_service: FilmService = DEFAULT_FILM_SERVICE,
) -> ResponseFilmDetailData:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Film not found",
        )

    return map_film_to_response(film)


@router.get(
    "/search/",
    response_model=List[ResponseFilmData],
    **film_search_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def films_search(
    request: Request,
    query: Annotated[
        str | None,
        Query(
            description="Поисковый запрос",
            example="Star Wars",
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
            description="Количество фильмов на странице",
            ge=1,
            le=100,
            example=10,
        ),
    ] = 10,
    labels: Annotated[
        Optional[List[str]],
        Query(
            alias="labels",
            description="Фильтр по меткам",
            example=["drama", "comedy"],
        ),
    ] = None,
    sort: Annotated[
        OrderByParams,
        Query(
            description=(
                "Сортировка по рейтингу IMDb: "
                "'imdb_rating' - по возрастанию, '-imdb_rating' - по убыванию"
            ),
            example="-imdb_rating",
        ),
    ] = None,
    film_service: FilmService = DEFAULT_FILM_SERVICE,
) -> Optional[List[ResponseFilmData]]:
    labels = labels if labels else []
    results = await film_service.search(query, sort, skip, limit, labels)
    return jsonable_encoder(
        [
            ResponseFilmData(
                uuid=item.id,
                title=item.title,
                imdb_rating=item.imdb_rating,
                labels=item.labels,
            )
            for item in results
        ],
    )


@router.get(
    "",
    response_model=List[ResponseFilmData],
    **films_listing_schema,
)
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def film_list(
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
            description="Количество фильмов на странице",
            ge=1,
            le=100,
            example=100,
        ),
    ] = 100,
    sort: Annotated[
        OrderByParams,
        Query(
            description=(
                "Сортировка по рейтингу IMDb: "
                "'imdb_rating' - по возрастанию, '-imdb_rating' - по убыванию"
            ),
            example="-imdb_rating",
        ),
    ] = None,
    genre_id: str = Query(
        description="Фильтр по ID жанра",
        example="120a21cf-9090-4e13-b139-616e477a0cd5",
        default="",
    ),
    film_service: FilmService = DEFAULT_FILM_SERVICE,
) -> Optional[List[ResponseFilmData]]:
    user = get_user_from_request(request)
    if user:
        results = await film_service.get_list(
            genre_id,
            sort,
            skip,
            limit,
            labels=["is_new"],
        )
    else:
        results = await film_service.get_list(
            genre_id,
            sort,
            skip,
            limit,
        )

    return jsonable_encoder(
        [
            ResponseFilmData(
                uuid=item.id,
                title=item.title,
                imdb_rating=item.imdb_rating,
                labels=item.labels,
            )
            for item in results
        ],
    )

import os
from http import HTTPStatus
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from auth_lib.utils import token_required
from content_service.src.api.cache import cache
from content_service.src.api.swagger import (
    films_by_person_schema,
    person_detail_schema,
    person_search_schema,
    persons_listing_schema,
)
from content_service.src.core import logger, settings
from content_service.src.schemas.movies.films import ResponseFilmData
from content_service.src.schemas.movies.persons import ResponsePersonData
from content_service.src.services.movies.persons import (
    PersonService,
    get_person_service,
)

DEFAULT_PERSON_SERVICE = Depends(get_person_service)
router = APIRouter()


@router.get(
    "/{person_id}",
    response_model=ResponsePersonData,
    **person_detail_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def person_details(
    request: Request,
    person_id: str,
    person_service: PersonService = DEFAULT_PERSON_SERVICE,
) -> ResponsePersonData:
    person = await person_service.get_by_id(person_id)
    if not person:
        # Если персонаж не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами,
        # которые содержат enum. Такой код будет более поддерживаемым
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Person not found",
        )

    # Перекладываем данные из models.Person в Person
    # Обратите внимание, что у модели бизнес-логики есть поле description,
    # которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования
    # ответов API, вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать
    return ResponsePersonData(uuid=person.id, name=person.name)


@router.get(
    "/search/",
    response_model=List[ResponsePersonData],
    **person_search_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def persons_search(
    request: Request,
    query: Annotated[
        str | None,
        Query(
            description="Поисковый запрос",
            example="Guy Ritchie",
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
            description="Количество персон на странице",
            ge=1,
            le=100,
            example=10,
        ),
    ] = 10,
    person_service: PersonService = DEFAULT_PERSON_SERVICE,
) -> Optional[List[ResponsePersonData]]:
    results = await person_service.search(query, skip, limit)
    return jsonable_encoder(
        [
            ResponsePersonData(
                uuid=item.id,
                name=item.name,
            )
            for item in results
        ],
    )


@router.get(
    "",
    response_model=List[ResponsePersonData],
    **persons_listing_schema,
)
@token_required
@logger.info(os.path.basename(__file__))
@cache(expire=settings.app.cache_ttl)
async def person_list(
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
            description="Количество персон на странице",
            ge=1,
            le=100,
            example=10,
        ),
    ] = 10,
    person_service: PersonService = DEFAULT_PERSON_SERVICE,
) -> Optional[List[ResponsePersonData]]:

    results = await person_service.get_list(skip, limit)
    return jsonable_encoder(
        [
            ResponsePersonData(
                uuid=item.id,
                name=item.name,
            )
            for item in results
        ],
    )


@router.get(
    "/{person_id}/films",
    response_model=List[ResponseFilmData],
    **films_by_person_schema,
)
@token_required
@cache(expire=settings.app.cache_ttl)
async def films_by_person_id(
    request: Request,
    person_id: str,
    person_service: PersonService = DEFAULT_PERSON_SERVICE,
) -> ResponsePersonData:
    films = await person_service.get_related_films_by_id(person_id)
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Films not found",
        )

    return jsonable_encoder(
        [
            ResponseFilmData(
                uuid=item.id,
                title=item.title,
                imdb_rating=item.imdb_rating,
                labels=item.labels,
            )
            for item in films
        ],
    )

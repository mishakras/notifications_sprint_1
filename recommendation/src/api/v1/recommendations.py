import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from recommendation.src.api.endpoint_descriptions import (
    RECOMMEND_DESCRIPTION,
    RECOMMEND_RESPONSES,
)
from recommendation.src.core import logger
from recommendation.src.schemas.movies.films import ResponseFilmDetailData
from recommendation.src.services.recomendation_service import (
    RecommendationService,
    get_recommendation_service,
)

router = APIRouter()


@router.post(
    "/recommend/",
    response_model=List[ResponseFilmDetailData],
    summary="Получить персонализированные рекомендации",
    description=RECOMMEND_DESCRIPTION,
    responses=RECOMMEND_RESPONSES,
)
@logger.info(os.path.basename(__file__))
async def create(
    user_id: str,
    search_list: List[str],
    recommendation_service: RecommendationService = Depends(
        get_recommendation_service,
    ),
):
    """
    Генерация персонализированных рекомендаций фильмов.

    Args:
        user_id: UUID пользователя для которого формируются рекомендации
        search_list: Список критериев для поиска рекомендаций
            (доступные значения: "directors", "actors", "writers", "genres")
        recommendation_service: Сервис для работы с рекомендациями

    Returns:
        List[ResponseFilmDetailData]: Список рекомендованных фильмов

    Raises:
        HTTPException: При ошибках валидации или отсутствии данных
    """
    # Валидация входных параметров
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id обязателен для формирования рекомендаций",
        )

    if not search_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="search_list не может быть пустым",
        )

    valid_search_fields = {"directors", "actors", "writers", "genres"}
    invalid_fields = set(search_list) - valid_search_fields

    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некорректные поля поиска: {', '.join(invalid_fields)}. "
            f"Допустимые значения: {', '.join(valid_search_fields)}",
        )

    search_config = {
        "directors": 1,
        "actors": 1,
        "writers": 1,
        "genres": 1,
    }
    search_values = {}

    for field in search_list:
        if search_config.get(field) is not None:
            search_values[field] = {}

    try:
        recommendations = await recommendation_service.get_recommendations(
            user_id=user_id,
            search_values=search_values,
        )

        if not recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рекомендации не найдены для данного пользователя",
            )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при формировании рекомендаций: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса рекомендаций",
        )

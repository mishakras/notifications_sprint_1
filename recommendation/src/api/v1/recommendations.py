from fastapi import APIRouter, Depends

from recommendation.src.api.endpoint_descriptions import (
    RECOMMEND_DESCRIPTION,
    RECOMMEND_RESPONSES,
)
from recommendation.src.core import logger
from recommendation.src.schemas.recommendation import RecommendRequest
from recommendation.src.services.recomendation_service import (
    RecommendationService,
    get_recommendation_service,
)

router = APIRouter()


@router.post(
    "/recommend/",
    summary="Получить персонализированные рекомендации",
    description=RECOMMEND_DESCRIPTION,
    responses=RECOMMEND_RESPONSES,
)
@logger.info(__name__)
async def create(
    payload: RecommendRequest,
    recommendation_service: RecommendationService = Depends(
        get_recommendation_service,
    ),
):
    """
    Сформировать рекомендации для пользователя.

    Поведение:
    - user_id валидируется как UUID (422 при невалидном значении).
    - search_list может быть пустым; используется whitelisting.
    - Возвращает список рекомендаций или None.
    """
    allowed = {"directors", "actors", "writers", "genres"}
    search_values: dict[str, dict] = {}
    for field in payload.search_list:
        if field in allowed:
            search_values[field] = {}

    result = await recommendation_service.get_recommendations(
        user_id=str(payload.user_id),
        search_values=search_values,
    )
    return result

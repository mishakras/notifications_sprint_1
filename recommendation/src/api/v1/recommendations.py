from fastapi import APIRouter, Depends

from recommendation.src.api.endpoint_descriptions import (
    RECOMMEND_DESCRIPTION,
    RECOMMEND_RESPONSES,
)
from recommendation.src.core import logger
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
    user_id: str,
    search_list: list[str],
    recommendation_service: RecommendationService = Depends(
        get_recommendation_service,
    ),
):
    search_config = {
        "directors": 1,
        "actors": 1,
        "writers": 1,
        "genres": 1,
    }
    search_values = {}
    for field in search_list:
        if search_config.get(field, None) is not None:
            search_values[field] = {}
    return await recommendation_service.get_recommendations(
        user_id=user_id,
        search_values=search_values,
    )

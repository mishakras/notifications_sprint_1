import os

from fastapi import APIRouter, Depends

from recommendation.src.core import logger
from recommendation.src.services.recomendation_service import (
    RecommendationService,
    get_recommendation_service,
)

router = APIRouter()


@router.post(
    "/recommend",
)
@logger.info(os.path.basename(__file__))
async def create(
    user_id: str,
    search_list: list[str],
    recommendation_service:
    RecommendationService = Depends(get_recommendation_service),
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
    await recommendation_service.get_recommendations(
        user_id=user_id,
        search_values=search_values
    )

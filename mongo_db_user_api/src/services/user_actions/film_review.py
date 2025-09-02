from beanie import PydanticObjectId

from mongo_db_user_api.src.repositories.user_actions.review_rep import (
    ReviewRepository,
    review_repository,
)
from mongo_db_user_api.src.schemas.likes import LikeReturn
from mongo_db_user_api.src.schemas.review import ReviewCreate, ReviewReturn
from mongo_db_user_api.src.services.base import BaseService


class ReviewService(BaseService):
    def __init__(self, repository: ReviewRepository):
        super().__init__(repository)
        self.repository = repository

    async def create(self, film_score_value: int | None, **kwargs):
        new_review = ReviewCreate(**kwargs)
        return await self.repository.create(
            data=new_review,
            film_score_value=film_score_value,
        )

    async def add_like(
        self,
        like_score_value: int,
        user_id: str,
        review_id: PydanticObjectId,
    ):
        return await self.repository.add_like(
            like_score_value=like_score_value,
            user_id=user_id,
            review_id=review_id,
        )

    async def get(self, document_id: PydanticObjectId):
        model = await self.repository.get(document_id)
        likes_total = 0
        likes_return = []
        for like in model.likes:
            likes_return.append(
                LikeReturn(
                    id=str(like.id),
                    created_at=like.created_at,
                    user_id=like.user_id,
                    score=like.score,
                ),
            )
            likes_total += like.score
        if len(model.likes):
            likes_total /= len(model.likes)
        return ReviewReturn(
            id=str(model.id),
            created_at=model.created_at,
            user_id=model.user_id,
            film_id=model.film_id,
            text=model.text,
            likes=likes_return,
            likes_total=likes_total,
        )


review_service = ReviewService(repository=review_repository)


async def get_review_service():
    yield review_service

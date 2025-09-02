from typing import Optional

from beanie import PydanticObjectId, WriteRules

from mongo_db_user_api.src.models.likes import Like
from mongo_db_user_api.src.models.review import Review
from mongo_db_user_api.src.repositories.beanie_repository import (
    BeanieRepository,
)
from mongo_db_user_api.src.repositories.user_actions.film_score_rep import (
    film_score_repository,
)
from mongo_db_user_api.src.schemas.film_score import FilmScoreCreate
from mongo_db_user_api.src.schemas.likes import LikeReturn
from mongo_db_user_api.src.schemas.review import (
    ReviewCreate,
    ReviewReturn,
    ReviewUpdate,
)


class ReviewRepository(
    BeanieRepository[Review, ReviewCreate, ReviewUpdate],
):
    async def create(
        self,
        data: ReviewCreate,
        film_score_value: int | None,
    ) -> Review:
        filters = {
            "user_id": {
                "comparison": "=",
                "value": data.user_id,
            },
            "film_id": {
                "comparison": "=",
                "value": data.film_id,
            },
        }
        model = await self.read(filters)
        if model is None:
            if film_score_value is None:
                film_score = await film_score_repository.read(filters)
            else:
                film_score = await film_score_repository.create(
                    FilmScoreCreate(
                        user_id=data.user_id,
                        film_id=data.film_id,
                        score=film_score_value,
                    ),
                )
            creation_data_dict = data.dict()
            creation_data_dict["score"] = film_score
            model_data = self.model_type(**creation_data_dict)
            await model_data.save(link_rule=WriteRules.WRITE)
            return model_data

    async def add_like(
        self,
        like_score_value: int,
        user_id: str,
        review_id: PydanticObjectId,
    ) -> Review | bool:
        model = await self.get(review_id)
        if model is not None:
            model.likes.append(
                Like(
                    user_id=user_id,
                    score=like_score_value,
                ),
            )
            await model.save(link_rule=WriteRules.WRITE)
            return model
        return False

    async def read_list_by_filter(
        self,
        filters=None,
        order: str = "id",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewReturn]:
        if filters is None:
            filters = {}
        filters_average_likes = None
        if filters["average_likes"]:
            filters_average_likes = filters["average_likes"]
            filters.pop("average_likes", None)
        models = (
            self.model_type.find(
                self.construct_filters(filters),
                fetch_links=True,
            )
            .skip(offset)
            .limit(limit)
            .sort(order)
        )
        return_models = []
        async for model in models:
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
                if filters_average_likes is not None:
                    return_model = self.check_average(
                        filters_average_likes,
                        likes_total,
                        model,
                        likes_return,
                    )
                    if return_model is not None:
                        return_models.append(return_model)
            else:
                return_models.append(
                    ReviewReturn(
                        id=str(model.id),
                        created_at=model.created_at,
                        user_id=model.user_id,
                        film_id=model.film_id,
                        text=model.text,
                        likes=likes_return,
                        average_likes=likes_total,
                    ),
                )
        return return_models

    def check_average(
        self,
        filters_average_likes,
        likes_total,
        model,
        likes_return,
    ) -> Optional[ReviewReturn] | None:
        return_model = None
        return_model_optional = ReviewReturn(
            id=str(model.id),
            created_at=model.created_at,
            user_id=model.user_id,
            film_id=model.film_id,
            text=model.text,
            likes=likes_return,
            average_likes=likes_total,
        )
        if filters_average_likes["comparison"] == ">":
            if likes_total > filters_average_likes["value"]:
                return return_model_optional
        if filters_average_likes["comparison"] == ">=":
            if likes_total >= filters_average_likes["value"]:
                return return_model_optional
        if filters_average_likes["comparison"] == "<":
            if likes_total < filters_average_likes["value"]:
                return return_model_optional
        if filters_average_likes["comparison"] == "<=":
            if likes_total <= filters_average_likes["value"]:
                return return_model_optional
        if filters_average_likes["comparison"] == "in":
            if (
                filters_average_likes["value_low"]
                < likes_total
                < filters_average_likes["value_high"]
            ):
                return return_model_optional
        if filters_average_likes["comparison"] == "=":
            if likes_total == filters_average_likes["value"]:
                return return_model_optional
        return return_model

    async def read(self, filters) -> Optional[ReviewReturn] | None:
        filters_average_likes = None
        if filters.get("average_likes"):
            filters_average_likes = filters["average_likes"]
            filters.pop("average_likes", None)
        model = await self.model_type.find(
            self.construct_filters(filters),
        ).first_or_none()
        if model is None:
            return None
        if not hasattr(model, "likes"):
            return ReviewReturn(
                id=str(model.id),
                created_at=model.created_at,
                user_id=model.user_id,
                film_id=model.film_id,
                text=model.text,
                likes=[],
                average_likes=0,
            )
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
            if filters_average_likes is not None:
                return self.check_average(
                    filters_average_likes,
                    likes_total,
                    model,
                    likes_return,
                )
            else:
                return None
        return ReviewReturn(
            id=str(model.id),
            created_at=model.created_at,
            user_id=model.user_id,
            film_id=model.film_id,
            text=model.text,
            likes=likes_return,
            average_likes=likes_total,
        )

    async def read_list(
        self,
        order: str = "id",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewReturn]:
        models = (
            self.model_type.find_all().skip(offset).limit(limit).sort(order)
        )
        return_models = []
        async for model in models:
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
            return_models.append(
                ReviewReturn(
                    id=str(model.id),
                    created_at=model.created_at,
                    user_id=model.user_id,
                    film_id=model.film_id,
                    text=model.text,
                    likes=likes_return,
                    average_likes=likes_total,
                ),
            )
        return return_models


review_repository = ReviewRepository(
    model=Review,
)

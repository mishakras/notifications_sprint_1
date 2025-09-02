from mongo_db_user_api.src.models.likes import Like
from mongo_db_user_api.src.repositories.beanie_repository import (
    BeanieRepository,
)
from mongo_db_user_api.src.schemas.likes import LikeCreate, LikeUpdate


class LikeRepository(
    BeanieRepository[Like, LikeCreate, LikeUpdate],
):
    pass


like_repository = LikeRepository(
    model=Like,
)

from typing import List, Optional

from .base import BaseTimestamp, MixinFilmID, MixinID, MixinUserID
from .likes import LikeReturn


class Review(BaseTimestamp, MixinUserID, MixinFilmID):
    text: str


class ReviewCreate(Review):
    pass


class ReviewUpdate(Review):
    pass


class ReviewAverage(Review):
    average_likes: Optional[float] = None
    pass


class ReviewReturn(ReviewAverage, MixinID):
    likes: Optional[List[LikeReturn]] = []

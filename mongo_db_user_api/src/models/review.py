from typing import List, Optional

from beanie import Document, Link

from .base import BaseTimestamp, MixinFilmID, MixinID, MixinUserID
from .film_score import FilmScore
from .likes import Like


class Review(Document, BaseTimestamp, MixinUserID, MixinFilmID, MixinID):
    text: str
    likes: Optional[List[Link[Like]]] = []
    score: Link[FilmScore]


class ReviewAverageLikes(BaseTimestamp, MixinUserID, MixinFilmID, MixinID):
    text: str
    average_likes: float

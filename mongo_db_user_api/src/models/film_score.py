from beanie import Document

from .base import BaseTimestamp, MixinFilmID, MixinID, MixinUserID


class FilmScore(Document, BaseTimestamp, MixinUserID, MixinFilmID, MixinID):
    score: int

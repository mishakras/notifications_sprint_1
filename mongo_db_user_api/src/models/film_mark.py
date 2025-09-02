from beanie import Document

from .base import BaseTimestamp, MixinFilmID, MixinID, MixinUserID


class FilmMark(Document, BaseTimestamp, MixinUserID, MixinFilmID, MixinID):
    pass

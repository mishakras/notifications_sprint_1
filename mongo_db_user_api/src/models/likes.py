from beanie import Document

from .base import BaseTimestamp, MixinID, MixinUserID


class Like(Document, BaseTimestamp, MixinUserID, MixinID):
    score: int

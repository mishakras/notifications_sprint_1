from .base import BaseTimestamp, MixinID, MixinUserID


class Like(BaseTimestamp, MixinUserID):
    score: int


class LikeCreate(Like):
    pass


class LikeUpdate(Like):
    pass


class LikeReturn(Like, MixinID):
    pass

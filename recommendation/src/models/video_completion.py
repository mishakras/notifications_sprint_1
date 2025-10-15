from beanie import Document

from .base import CreateMixin, MixinFilmID, MixinID, MixinUserID


class VideoCompletion(MixinUserID, MixinFilmID):
    duration: float
    watched_percentage: float


class VideoCompletionDB(Document, VideoCompletion, MixinID):
    pass


class VideoCompletionCreate(CreateMixin, VideoCompletion):
    pass


class VideoCompletionUpdate(VideoCompletion):
    pass

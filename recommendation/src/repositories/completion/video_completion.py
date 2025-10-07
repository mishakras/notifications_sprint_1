from recommendation.src.models.video_completion import (
    VideoCompletionCreate,
    VideoCompletionDB,
    VideoCompletionUpdate,
)
from recommendation.src.repositories.beanie_repository import BeanieRepository


class VideoCompletionRepository(
    BeanieRepository[
        VideoCompletionDB,
        VideoCompletionCreate,
        VideoCompletionUpdate,
    ],
):
    pass


video_completion_repository = VideoCompletionRepository(
    model=VideoCompletionDB,
)

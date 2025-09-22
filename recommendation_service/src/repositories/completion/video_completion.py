from recommendation_service.src.models.video_completion import (
    VideoCompletionDB,
    VideoCompletionCreate,
    VideoCompletionUpdate
)
from recommendation_service.src.repositories.beanie_repository import (
    BeanieRepository,
)



class VideoCompletionRepository(
    BeanieRepository[VideoCompletionDB, VideoCompletionCreate, VideoCompletionUpdate],
):
    pass


video_completion_repository = VideoCompletionRepository(
    model=VideoCompletionDB,
)

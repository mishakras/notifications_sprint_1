from recommendation_service.src.repositories.completion.video_completion import (
    video_completion_repository,
)
from recommendation_service.src.services.base_service import BaseBeanieService


class VideoCompletionService(BaseBeanieService):
    pass


video_completion_service = VideoCompletionService(repository=video_completion_repository)


def get_video_completion_service() -> VideoCompletionService:
    yield video_completion_service

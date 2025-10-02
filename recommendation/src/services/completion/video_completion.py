from src.repositories.completion.video_completion import (
    video_completion_repository,
)
from src.services.base_service import BaseBeanieService


class VideoCompletionService(BaseBeanieService):
    pass


def get_video_completion_service() -> VideoCompletionService:
    return VideoCompletionService(
        repository=video_completion_repository,
    )

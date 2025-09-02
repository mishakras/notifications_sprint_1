__all__ = ("router",)

from fastapi import APIRouter

from .click import router as click_router
from .page_view import router as page_view_router
from .search_filter import router as search_filter_router
from .video_completion import router as video_completion_router
from .video_quality import router as video_quality_router

router = APIRouter(prefix="/api/v1/ugc")
router.include_router(page_view_router)
router.include_router(click_router)
router.include_router(search_filter_router)
router.include_router(video_quality_router)
router.include_router(video_completion_router)

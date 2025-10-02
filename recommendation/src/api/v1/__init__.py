__all__ = ("router",)

from fastapi import APIRouter

from .recommendations import router as rec_router

router = APIRouter()
router.include_router(rec_router)

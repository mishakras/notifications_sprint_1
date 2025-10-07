__all__ = ("router",)

from fastapi import APIRouter

from .v1 import router as v1_router

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["recommendations"],
)
router.include_router(v1_router)

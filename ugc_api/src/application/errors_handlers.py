import traceback

from app.src.core import settings
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse


def register_errors_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    def error_handler(request: Request, exc: Exception):  # noqa: U100
        if isinstance(exc, HTTPException):
            detail = exc.detail
        else:
            detail = str(exc)
        if settings.app.debug:
            return JSONResponse(
                content={
                    "detail": detail,
                    "traceback": traceback.format_exc(),
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        raise exc

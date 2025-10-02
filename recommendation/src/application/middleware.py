from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from src.core import settings


def add_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def before_request(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id")

        if not request_id:
            if settings.app.environment != settings.dev:
                return ORJSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "X-Request-Id is required"},
                )
            else:
                request_id = str(settings.app.zero_request_id)

        response = await call_next(request)

        response.headers["X-Request-Id"] = request_id
        return response

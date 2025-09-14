from fastapi import Depends, FastAPI, Request, WebSocket, status
from fastapi.responses import ORJSONResponse

from websocket.src.api.websocket.v1 import websocket
from websocket.src.core import settings
from websocket.src.websocket_notiff_service.websocket_server import (
    ConnectionManager,
    get_connection_manager,
)

app = FastAPI(
    title=settings.app.title,
    docs_url="/api/v1/openapi",
    openapi_url="/api/v1/openapi.json",
    default_response_class=ORJSONResponse,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@app.middleware("http")
async def before_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id")

    if not request_id:
        if settings.app.environment != settings.envEnum.DEVELOPMENT:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        else:
            request_id = str(settings.app.zero_request_id)

    response = await call_next(request)

    response.headers["X-Request-Id"] = request_id
    return response


@app.websocket("/ws")
async def websocket_endpoint(
    app_websocket: WebSocket,
    manager: ConnectionManager = Depends(get_connection_manager),
):
    await manager.connect(app_websocket)


app.include_router(
    websocket.router,
    prefix="/api/v1/websocket",
    tags=["websocket"],
)

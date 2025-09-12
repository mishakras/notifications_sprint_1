import websockets
from fastapi import HTTPException, WebSocket, WebSocketDisconnect, status
from starlette.status import HTTP_404_NOT_FOUND

from auth_service.src.auth.auth import decode_token


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        try:
            token = await websocket.receive_text()
        except websockets.exceptions.ConnectionClosed:
            return
        try:
            user = decode_token(token)
            self.active_connections[user["sub"]] = websocket
            self.active_connections["test"] = websocket
            try:
                while True:
                    await websocket.receive_json()
            except WebSocketDisconnect:
                self.disconnect(user["sub"])
            # Отправить все старые уведомления.
        except HTTPException as e:
            if e.status_code == status.HTTP_401_UNAUTHORIZED:
                try:
                    await websocket.send_text("Не валидный токен")
                    return
                except websockets.exceptions.ConnectionClosed:
                    return

    def disconnect(self, user_sub: str):
        self.active_connections.pop(user_sub, None)

    async def send_personal_message(self, message: str, user_sub: str):
        websocket = self.active_connections.get(user_sub, None)
        if websocket is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Пользователь не подключен",
            )
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            self.disconnect(user_sub)
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Пользователь отключился",
            )

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


connection_manager = ConnectionManager()


async def get_connection_manager():
    yield connection_manager

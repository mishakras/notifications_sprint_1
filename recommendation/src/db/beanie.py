from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

client: Optional[AsyncIOMotorClient] = None


# Функция понадобится при внедрении зависимостей
async def get_beanie() -> AsyncIOMotorClient:
    return client

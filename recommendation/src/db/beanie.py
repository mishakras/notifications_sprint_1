from motor.motor_asyncio import AsyncIOMotorClient

client: AsyncIOMotorClient | None = None


# Функция понадобится при внедрении зависимостей
async def get_beanie() -> AsyncIOMotorClient:
    return client

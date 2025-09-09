from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from src.core import settings

# Настройка подключения к Postgres
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres.user}:"
    f"{settings.postgres.password}@{settings.postgres.host}/"
    f"{settings.postgres.database}"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()


async def get_db_session():
    """Получение асинхронной сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

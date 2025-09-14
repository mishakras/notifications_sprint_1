from asyncio import current_task
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from yarl import URL

from notification_service.src.core import settings

DATABASE_WITH_TABLE_URL = str(
    URL.build(
        scheme="postgresql+asyncpg",
        user=settings.postgres.user,
        password=settings.postgres.password,
        host=settings.postgres.host,
        path=f"/{settings.postgres.path}",
    ),
)

Base = declarative_base()


class DatabaseHelper:
    def __init__(self, url: str):
        self.engine = create_async_engine(url=url, echo=True)

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_scope_session(self) -> async_scoped_session:
        return async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )

    @asynccontextmanager
    async def get_db_session(self) -> AsyncSession:
        from sqlalchemy import exc

        session: AsyncSession = self.session_factory()
        try:
            yield session
        except exc.SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


db_helper = DatabaseHelper(DATABASE_WITH_TABLE_URL)

from typing import Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.src.db.postgres import Base
from auth_service.src.repositories.base_repository import AbstractRepository

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SqlAlchemyRepository(
    AbstractRepository,
    Generic[ModelType, CreateSchemaType, UpdateSchemaType],
):

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.db_session = db_session
        self.model = model

    async def create(self, data: CreateSchemaType) -> ModelType:
        async with self.db_session() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.commit()
            primary_key = next(
                iter(self.model.__table__.primary_key.columns),
            ).name

            result = await session.execute(
                select(self.model).where(
                    getattr(
                        self.model,
                        primary_key,
                    )
                    == getattr(instance, primary_key),
                ),
            )
            instance = result.scalar()
            return instance

    async def update(self, data: UpdateSchemaType, **filters) -> ModelType:
        async with self.db_session() as session:
            res = await session.execute(
                update(
                    self.model,
                )
                .values(**data)
                .filter_by(**filters)
                .returning(self.model),
            )
            await session.commit()
            return res.scalars().first()

    async def delete(self, **filters) -> None:
        async with self.db_session() as session:
            await session.execute(delete(self.model).filter_by(**filters))
            await session.commit()

    async def read(self, **filters) -> Optional[ModelType] | None:
        async with self.db_session() as session:
            row = await session.execute(
                select(self.model).filter_by(**filters),
            )
            return row.scalars().first()

    async def read_list(
        self,
        order: str = "id",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        async with self.db_session() as session:
            stmt = (
                select(
                    self.model,
                )
                .order_by(
                    *order,
                )
                .limit(limit)
                .offset(offset),
            )
            row = await session.execute(stmt)
            return row.scalars().all()

    async def read_list_by_filter(
        self,
        **filters,
    ) -> list[ModelType]:
        async with self.db_session() as session:
            stmt = select(self.model).filter_by(**filters)
            row = await session.execute(stmt)
            return row.scalars().all()

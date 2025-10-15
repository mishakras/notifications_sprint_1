from beanie import Document, PydanticObjectId
from pydantic import BaseModel

from .base_repository import AbstractRepository


class BeanieRepository[
    ModelType: Document,
    CreateSchemaType: BaseModel,
    UpdateSchemaType: BaseModel,
](AbstractRepository):

    def __init__(self, model: type[ModelType]):
        self.model_type = model

    async def get(self, document_id: PydanticObjectId) -> ModelType:
        model = await self.model_type.get(document_id)
        return model

    async def create(self, data: CreateSchemaType) -> ModelType:
        model = self.model_type(**data.model_dump())
        await model.insert()
        return model

    async def update(self, data: UpdateSchemaType, filters) -> ModelType:
        model_new_data = self.model_type(**data.model_dump())
        model = await self.model_type.find_one(self.construct_filters(filters))
        await model.update(**model_new_data.dict())
        return model

    async def delete(self, filters) -> bool:
        result = await self.model_type.find_one(filters).delete()
        return result.deleted_count > 0

    async def read(self, filters) -> ModelType | None:
        return await self.model_type.find(
            self.construct_filters(filters),
        ).first_or_none()

    async def read_list(
        self,
        order: str = "id",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        return (
            await self.model_type.find_all()
            .skip(offset)
            .limit(limit)
            .sort(order)
            .to_list()
        )

    async def read_list_by_filter(
        self,
        filters=None,
        order: str = "id",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        if filters is None:
            filters = {}
        return (
            await self.model_type.find(
                self.construct_filters(filters),
            )
            .skip(offset)
            .limit(limit)
            .sort(order)
            .to_list()
        )

    @staticmethod
    def construct_filters(filters: dict):
        filers_dict = {}
        for field, filter_vals in filters.items():
            if filter_vals["comparison"] == ">":
                filers_dict[field] = {"$gt": filter_vals["value"]}
            if filter_vals["comparison"] == ">=":
                filers_dict[field] = {"$gte": filter_vals["value"]}
            if filter_vals["comparison"] == "<":
                filers_dict[field] = {"$lt": filter_vals["value"]}
            if filter_vals["comparison"] == "<=":
                filers_dict[field] = {"$lte": filter_vals["value"]}
            if filter_vals["comparison"] == "in":
                filers_dict[field] = {"$in": filter_vals["value"]}
            if filter_vals["comparison"] == "=":
                filers_dict[field] = {"$eq": filter_vals["value"]}
        return filers_dict

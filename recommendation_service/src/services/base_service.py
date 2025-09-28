from typing import Optional

from beanie import PydanticObjectId
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis

from recommendation_service.src.repositories.beanie_repository import BeanieRepository


class BaseElasticService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def _elastic_search(self, index: str, body: dict) -> Optional[list]:
        try:
            search_results = await self.elastic.search(
                index=index,
                body=body,
            )
        except Exception:
            return None

        documents = search_results["hits"]["hits"]
        results = [doc["_source"] for doc in documents]

        if not results:
            return []

        return results


class BaseBeanieService:
    def __init__(self, repository: BeanieRepository):
        self.repository = repository

    async def get_list(
            self,
            filters,
            order: str = "id",
            limit: int = 100,
            offset: int = 0,
    ):
        return await self.repository.read_list_by_filter(
            order=order,
            limit=limit,
            offset=offset,
            filters=filters,
        )

    async def get(self, document_id: PydanticObjectId):
        return await self.repository.get(document_id)

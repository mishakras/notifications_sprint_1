from typing import Optional

from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis


class BaseService:
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

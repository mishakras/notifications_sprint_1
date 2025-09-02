from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from content_service.src.db.elastic import get_elastic
from content_service.src.db.redis import get_redis
from content_service.src.schemas.movies.genres import Genre
from content_service.src.services.movies.service import BaseService

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
DEFAULT_REDIS = Depends(get_redis)
DEFAULT_ELASTIC = Depends(get_elastic)


class GenreService(BaseService):
    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        genre = await self._get_genre_from_elastic(genre_id)
        if not genre:
            return None

        return genre

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc["_source"])

    async def search(
        self,
        query: Optional[str],
        skip: int,
        limit: int,
    ) -> Optional[List[Genre]]:
        query_body = {
            "query": (
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["*"],
                        "fuzziness": "AUTO",
                    },
                }
                if query
                else {"match_all": {}}
            ),
            "size": limit,
            "from": skip,
        }

        documents = await self._elastic_search("genres", query_body)
        if documents:
            results = [Genre(**doc) for doc in documents]
            return results
        else:
            return []

    async def get_list(
        self,
        skip: int,
        limit: int,
    ) -> Optional[List[Genre]]:

        filter_query = {"match_all": {}}

        query_body = {
            "query": filter_query,
            "from": skip,
            "size": limit,
        }

        documents = await self._elastic_search("genres", query_body)
        if documents:
            results = [Genre(**doc) for doc in documents]
            return results
        else:
            return []


def get_genre_service(
    redis: Redis = DEFAULT_REDIS,
    elastic: AsyncElasticsearch = DEFAULT_ELASTIC,
) -> GenreService:
    return GenreService(redis, elastic)

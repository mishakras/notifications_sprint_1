from typing import List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from content_service.src.db.elastic import get_elastic
from content_service.src.db.redis import get_redis
from content_service.src.schemas.movies.films import Film
from content_service.src.schemas.movies.persons import Person
from content_service.src.services.movies.service import BaseService

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
DEFAULT_REDIS = Depends(get_redis)
DEFAULT_ELASTIC = Depends(get_elastic)


class PersonService(BaseService):
    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._get_person_from_elastic(person_id)
        if not person:
            return None

        return person

    async def _get_person_from_elastic(
        self,
        person_id: str,
    ) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None
        return Person(**doc["_source"])

    async def search(
        self,
        query: Optional[str],
        skip: int,
        limit: int,
    ) -> Optional[List[Person]]:
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

        documents = await self._elastic_search("persons", query_body)
        if documents:
            results = [Person(**doc) for doc in documents]
            return results
        else:
            return []

    async def get_list(
        self,
        skip: int,
        limit: int,
    ) -> Optional[List[Person]]:

        filter_query = {"match_all": {}}

        query_body = {
            "query": filter_query,
            "from": skip,
            "size": limit,
        }

        documents = await self._elastic_search("persons", query_body)
        if documents:
            results = [Person(**doc) for doc in documents]
            return results
        else:
            return []

    async def get_related_films_by_id(
        self,
        person_id: Optional[UUID],
    ) -> Optional[List[Film]]:
        query_body = {"match_all": {}}
        if person_id:
            query_body = {
                "query": {
                    "bool": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {
                                        "nested": {
                                            "path": "directors",
                                            "query": {
                                                "term": {
                                                    "directors.id": str(
                                                        person_id,
                                                    ),
                                                },
                                            },
                                        },
                                    },
                                    {
                                        "nested": {
                                            "path": "actors",
                                            "query": {
                                                "term": {
                                                    "actors.id": str(
                                                        person_id,
                                                    ),
                                                },
                                            },
                                        },
                                    },
                                    {
                                        "nested": {
                                            "path": "writers",
                                            "query": {
                                                "term": {
                                                    "writers.id": str(
                                                        person_id,
                                                    ),
                                                },
                                            },
                                        },
                                    },
                                ],
                                "minimum_should_match": 1,
                            },
                        },
                    },
                },
            }

        documents = await self._elastic_search("movies", query_body)
        if documents:
            results = [Film(**doc) for doc in documents]
            return results
        else:
            return []


def get_person_service(
    redis: Redis = DEFAULT_REDIS,
    elastic: AsyncElasticsearch = DEFAULT_ELASTIC,
) -> PersonService:
    return PersonService(redis, elastic)

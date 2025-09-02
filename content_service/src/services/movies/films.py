from typing import List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from content_service.src.db.elastic import get_elastic
from content_service.src.db.redis import get_redis
from content_service.src.schemas.movies.films import Film
from content_service.src.services.movies.service import BaseService

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
DEFAULT_REDIS = Depends(get_redis)
DEFAULT_ELASTIC = Depends(get_elastic)


class FilmService(BaseService):
    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._get_film_from_elastic(film_id)
        if not film:
            return None

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return Film(**doc["_source"])

    async def search(
        self,
        query: Optional[str],
        sort: Optional[str],
        skip: int,
        limit: int,
        labels: bool,
    ) -> Optional[List[Film]]:
        query_body = {
            "query": {
                "bool": {
                    "must": (
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
                    "filter": (
                        [
                            {
                                "bool": {
                                    "must": [
                                        {"term": {"labels": label}}
                                        for label in labels
                                    ],
                                },
                            },
                        ]
                        if labels
                        else []
                    ),
                },
            },
            "size": limit,
            "from": skip,
        }

        if sort:
            (sort_field, sort_order) = (
                (
                    sort[1:],
                    "desc",
                )
                if sort.startswith("-")
                else (
                    sort,
                    "asc",
                )
            )

            query_body["sort"] = [{sort_field: sort_order}]

        documents = await self._elastic_search("movies", query_body)
        if documents:
            results = [Film(**doc) for doc in documents]
            return results
        else:
            return []

    async def get_list(
        self,
        genre_id: Optional[UUID],
        sort: Optional[str],
        skip: int,
        limit: int,
        labels=None,
    ) -> Optional[List[Film]]:
        filter_query = {"match_all": {}}
        if genre_id:
            filter_query = {
                "bool": {
                    "filter": {
                        "bool": {
                            "should": [
                                {
                                    "nested": {
                                        "path": "genres",
                                        "query": {
                                            "term": {
                                                "genres.id": str(genre_id),
                                            },
                                        },
                                    },
                                },
                            ],
                            "minimum_should_match": 1,
                        },
                    },
                },
            }

        query_body = {
            "query": filter_query,
            "from": skip,
            "size": limit,
        }

        if sort:
            (sort_field, sort_order) = (
                (
                    sort[1:],
                    "desc",
                )
                if sort.startswith("-")
                else (
                    sort,
                    "asc",
                )
            )

            query_body["sort"] = [{sort_field: sort_order}]

        if labels:
            query_body["query"] = {
                "bool": {
                    "must": [filter_query],
                    "filter": [
                        {
                            "terms": {
                                "labels": (
                                    labels
                                    if isinstance(labels, list)
                                    else [labels]
                                ),
                            },
                        },
                    ],
                },
            }
        else:
            query_body["query"] = {
                "bool": {
                    "must": [filter_query],
                    "must_not": [{"terms": {"labels": ["is_new"]}}],
                },
            }
        documents = await self._elastic_search("movies", query_body)
        if documents:
            results = [Film(**doc) for doc in documents]
            return results
        else:
            return []


def get_film_service(
    redis: Redis = DEFAULT_REDIS,
    elastic: AsyncElasticsearch = DEFAULT_ELASTIC,
) -> FilmService:
    return FilmService(redis, elastic)

from typing import List, Optional

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from recommendation_service.src.core import settings
from recommendation_service.src.db.elastic import get_elastic
from recommendation_service.src.db.redis import get_redis
from recommendation_service.src.schemas.movies.films import Film
from recommendation_service.src.services.cache import cache
from recommendation_service.src.services.base_service import BaseElasticService

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
DEFAULT_REDIS = Depends(get_redis)
DEFAULT_ELASTIC = Depends(get_elastic)


def construct_filters(search_values: dict):
    filter_should = []
    for field, items in search_values.items():
        filter_should.append(
            {
                "nested": {
                    "path": field,
                    "query": {
                        "terms": {
                            field + ".id": [items.keys()]
                        }
                    }
                }
            }
        )
    return filter_should


def construct_functions(search_values):
    functions = []
    for field, items in search_values.items():
        for item, value in items.items():
            functions.append(
                {
                    "filter": {
                        "nested": {
                            "path": field,
                            "query": {
                                "terms": {
                                    field + ".id": item
                                }
                            }
                        }
                    },
                    "script_score": {
                        "script": {
                            "params": {
                                "a": value,
                            },
                            "source": "params.a*film['imdb_rating'].value/2"
                        }
                    }
                }
            )
    return functions


class FilmService(BaseElasticService):

    @cache(expire=settings.app.cache_ttl)
    async def search_by_ids(
        self,
        ids: list[str],
        limit: int,
    ) -> Optional[List[Film]]:
        query_body = {
            "query": {
                "ids": {
                    "values": ids
                }
            },
            "size": limit,
        }

        documents = await self._elastic_search("movies", query_body)
        if documents:
            results = [Film(**doc) for doc in documents]
            return results
        else:
            return []

    @cache(expire=settings.app.cache_ttl / 10)
    async def search_similar(
        self,
        search_values: dict,
        ids: list[str],
    ) -> Optional[List[Film]]:
        query_body = {
            "boosting": {
                "positive": {
                    "function_score": {
                        "query": {
                            "filtered": {
                                "bool": {
                                    "should": construct_filters(search_values)
                                }
                            }
                        },
                        "functions": [
                            construct_functions(search_values)
                        ],
                        "boost_mode": "sum",
                    }
                },
                "negative": {
                    "ids": {
                        "values": ids
                    }
                },
                "negative_boost": 0.01
            }
        }

        documents = await self._elastic_search("movies", query_body)
        if documents:
            results = [Film(**doc) for doc in documents]
            return results
        return []


def get_film_service(
    redis: Redis = DEFAULT_REDIS,
    elastic: AsyncElasticsearch = DEFAULT_ELASTIC,
) -> FilmService:
    return FilmService(redis, elastic)

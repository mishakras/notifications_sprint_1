from __future__ import annotations
from typing import Optional, Sequence

from elasticsearch import AsyncElasticsearch


class ES:
    def __init__(
        self,
        host: str,
        index: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        basic_auth = (user, password) if user and password else None
        self._es = AsyncElasticsearch(
            hosts=[host],
            basic_auth=basic_auth,
            request_timeout=30,
        )
        self._index = index

    async def __aenter__(self) -> "ES":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._es.close()

    async def close(self) -> None:
        await self._es.close()

    async def fetch_by_ids(self, ids: Sequence[str]) -> list[dict]:
        """Вернуть фильмы по списку id в исходном порядке."""
        if not ids:
            return []
        response = await self._es.mget(
            index=self._index,
            body={"ids": list(ids)},
        )
        documents: list[dict] = []
        for doc in response.get("docs", []):
            if doc.get("found"):
                src = doc.get("_source", {}) or {}
                src["_id"] = doc.get("_id")
                documents.append(src)
        return documents

    async def rank_by_genres(
        self,
        genre_ids: Sequence[str],
        limit: int = 100,
    ) -> list[dict]:
        """Ранжирование по количеству совпавших жанров (genres.id)."""
        if not genre_ids:
            return []
        script_src = (
            "int c = 0;"
            "if (doc.containsKey('genres.id')"
            " && !doc['genres.id'].isEmpty()) {"
            "  for (def t : doc['genres.id']) {"
            "    if (params.gs.contains(t)) { c++; }"
            "  }"
            "}"
            "double r = (doc.containsKey('rating')"
            " && !doc['rating'].isEmpty())"
            "  ? doc['rating'].value : 0.0;"
            "return c + r/100.0;"
        )
        query = {
            "script_score": {
                "query": {
                    "bool": {
                        "filter": {
                            "terms": {
                                "genres.id": list(genre_ids),
                            },
                        },
                    },
                },
                "script": {
                    "lang": "painless",
                    "source": script_src,
                    "params": {
                        "gs": list(genre_ids),
                    },
                },
            },
        }
        response = await self._es.search(
            index=self._index,
            size=limit,
            query=query,
        )
        hits = response.get("hits", {}).get("hits", [])
        result: list[dict] = []
        for hit in hits:
            src = dict(hit["_source"])
            src["_id"] = hit["_id"]
            src["_score"] = hit["_score"]
            result.append(src)
        return result

    async def rank_by_persons(
        self,
        actor_ids: Sequence[str] | None,
        director_ids: Sequence[str] | None,
        limit: int = 100,
        director_weight: int = 2,
    ) -> list[dict]:
        """Ранжирование по актёрам/режиссёрам с весом режиссёров."""
        actor_ids = list(actor_ids or [])
        director_ids = list(director_ids or [])
        if not actor_ids and not director_ids:
            return []
        should_parts: list[dict] = []
        if actor_ids:
            should_parts.append({"terms": {"actors.id": actor_ids}})
        if director_ids:
            should_parts.append({"terms": {"directors.id": director_ids}})
        base_query = {
            "bool": {
                "should": should_parts,
                "minimum_should_match": 1,
            },
        }
        script_src = (
            "int ca = 0; int cd = 0;"
            "if (doc.containsKey('actors.id')"
            " && !doc['actors.id'].isEmpty()) {"
            "  for (def t : doc['actors.id']) {"
            "    if (params.actors.contains(t)) { ca++; }"
            "  }"
            "}"
            "if (doc.containsKey('directors.id')"
            " && !doc['directors.id'].isEmpty()) {"
            "  for (def t : doc['directors.id']) {"
            "    if (params.directors.contains(t)) { cd++; }"
            "  }"
            "}"
            "return ca + params.dw * cd;"
        )
        query = {
            "script_score": {
                "query": base_query,
                "script": {
                    "lang": "painless",
                    "source": script_src,
                    "params": {
                        "actors": actor_ids,
                        "directors": director_ids,
                        "dw": director_weight,
                    },
                },
            },
        }
        response = await self._es.search(
            index=self._index,
            size=limit,
            query=query,
        )
        hits = response.get("hits", {}).get("hits", [])
        result: list[dict] = []
        for hit in hits:
            src = dict(hit["_source"])
            src["_id"] = hit["_id"]
            src["_score"] = hit["_score"]
            result.append(src)
        return result

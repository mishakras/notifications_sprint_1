from __future__ import annotations
import asyncio
from typing import Sequence, Optional
from elasticsearch import AsyncElasticsearch
from settings import SETTINGS

class ES:
    def __init__(self, host: str, index: str, user: Optional[str] = None, password: Optional[str] = None):
        # Если в проекте включена безопасность — можно пробросить basic_auth
        basic_auth = (user, password) if user and password else None
        self._es = AsyncElasticsearch(
            hosts=[host],
            basic_auth=basic_auth,
            request_timeout=30,
        )
        self._index = index

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._es.close()

    async def close(self):
        await self._es.close()

    async def fetch_by_ids(self, ids: Sequence[str]) -> list[dict]:
        """Быстрый возврат фильмов по списку id в исходном порядке."""
        if not ids:
            return []
        resp = await self._es.mget(index=self._index, body={"ids": list(ids)})
        docs = []
        for d in resp.get("docs", []):
            if d.get("found"):
                src = d.get("_source", {}) or {}
                src["_id"] = d.get("_id")
                docs.append(src)
        return docs

    async def rank_by_genres(self, genre_ids: Sequence[str], limit: int = 100) -> list[dict]:
        """Ранжирование по количеству совпавших жанров (genres.id) + лёгкая подмешка rating."""
        if not genre_ids:
            return []

        query = {
            "script_score": {
                "query": {
                    "bool": {
                        "filter": {
                            "terms": {"genres.id": list(genre_ids)}
                        }
                    }
                },
                "script": {
                    "lang": "painless",
                    "source": """
                        int c = 0;
                        if (doc.containsKey('genres.id') && !doc['genres.id'].isEmpty()) {
                          for (def t : doc['genres.id']) {
                            if (params.gs.contains(t)) { c++; }
                          }
                        }
                        double r = (doc.containsKey('rating') && !doc['rating'].isEmpty())
                          ? doc['rating'].value : 0.0;
                        return c + r/100.0;
                    """,
                    "params": {"gs": list(genre_ids)}
                }
            }
        }

        resp = await self._es.search(index=self._index, size=limit, query=query)
        hits = resp.get("hits", {}).get("hits", [])
        return [dict(h["_source"], **{"_id": h["_id"], "_score": h["_score"]}) for h in hits]

    async def rank_by_persons(
        self,
        actor_ids: Sequence[str] | None,
        director_ids: Sequence[str] | None,
        limit: int = 100,
        director_weight: int = 2
    ) -> list[dict]:
        """Ранжирование по совпадениям актёров/режиссёров (actors.id / directors.id) с весом режиссёров."""
        actor_ids = list(actor_ids or [])
        director_ids = list(director_ids or [])
        if not actor_ids and not director_ids:
            return []

        base_query = {
            "bool": {
                "should": [q for q in [
                    {"terms": {"actors.id": actor_ids}} if actor_ids else None,
                    {"terms": {"directors.id": director_ids}} if director_ids else None,
                ] if q],
                "minimum_should_match": 1
            }
        }

        query = {
            "script_score": {
                "query": base_query,
                "script": {
                    "lang": "painless",
                    "source": """
                        int ca = 0; int cd = 0;
                        if (doc.containsKey('actors.id') && !doc['actors.id'].isEmpty()) {
                          for (def t : doc['actors.id']) { if (params.actors.contains(t)) { ca++; } }
                        }
                        if (doc.containsKey('directors.id') && !doc['directors.id'].isEmpty()) {
                          for (def t : doc['directors.id']) { if (params.directors.contains(t)) { cd++; } }
                        }
                        return ca + params.dw * cd;
                    """,
                    "params": {"actors": actor_ids, "directors": director_ids, "dw": director_weight}
                }
            }
        }

        resp = await self._es.search(index=self._index, size=limit, query=query)
        hits = resp.get("hits", {}).get("hits", [])
        return [dict(h["_source"], **{"_id": h["_id"], "_score": h["_score"]}) for h in hits]


async def _demo():
    es = ES(SETTINGS.es_host, SETTINGS.es_index)
    try:
        print(await es.fetch_by_ids([]))
    finally:
        await es.close()

if __name__ == "__main__":
    asyncio.run(_demo())

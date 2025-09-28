from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from elasticsearch import AsyncElasticsearch


def _as_list(values: Iterable[str]) -> List[str]:
    return list({str(v) for v in values if v})


class ES:
    def __init__(self, host: str, index: str) -> None:
        self._es = AsyncElasticsearch(hosts=[host], request_timeout=30)
        self._index = index

    async def __aenter__(self) -> "ES":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._es.close()

    async def fetch_by_ids(self, ids: Sequence[str]) -> list[dict]:
        ids_list = _as_list(ids)
        if not ids_list:
            return []
        resp = await self._es.mget(index=self._index, body={"ids": ids_list})
        docs = []
        for d in resp.get("docs", []):
            if d.get("found"):
                src = d.get("_source", {}) or {}
                src["_id"] = d.get("_id")
                docs.append(src)
        return docs

    async def rank_by_profile(
        self,
        genre_weights: Dict[str, float],
        actor_weights: Dict[str, float],
        director_weights: Dict[str, float],
        *,
        exclude_ids: Optional[Sequence[str]] = None,
        limit: int = 100,
        director_weight: float = 2.0,
        rating_weight: float = 0.0,
    ) -> list[dict]:
        should: List[dict] = []
        if genre_weights:
            should.append(
                {"nested": {
                    "path": "genres",
                    "query": {"terms": {"genres.id": list(genre_weights.keys())}},
                }}
            )
        if actor_weights:
            should.append(
                {"nested": {
                    "path": "actors",
                    "query": {"terms": {"actors.id": list(actor_weights.keys())}},
                }}
            )
        if director_weights:
            should.append(
                {"nested": {
                    "path": "directors",
                    "query": {"terms": {"directors.id": list(director_weights.keys())}},
                }}
            )

        base_query = {
            "bool": {
                "must_not": [{"ids": {"values": list(exclude_ids)}}] if exclude_ids else [],
                "should": should,
                "minimum_should_match": 1 if should else 0,
            }
        }

        script = """
            double s = 0.0;
            if (!params.gw.isEmpty() && doc.containsKey('genres.id') && !doc['genres.id'].isEmpty()) {
              for (def v : doc['genres.id']) { if (params.gw.containsKey(v)) s += (double)params.gw.get(v); }
            }
            if (!params.aw.isEmpty() && doc.containsKey('actors.id') && !doc['actors.id'].isEmpty()) {
              for (def v : doc['actors.id']) { if (params.aw.containsKey(v)) s += (double)params.aw.get(v); }
            }
            if (!params.dw.isEmpty() && doc.containsKey('directors.id') && !doc['directors.id'].isEmpty()) {
              for (def v : doc['directors.id']) { if (params.dw.containsKey(v)) s += params.dcoef * (double)params.dw.get(v); }
            }
            if (params.rcoef != 0.0 && doc.containsKey('rating') && !doc['rating'].isEmpty()) {
              s += params.rcoef * (double)doc['rating'].value;
            }
            return s;
        """

        query = {
            "script_score": {
                "query": base_query,
                "script": {
                    "lang": "painless",
                    "source": script,
                    "params": {
                        "gw": genre_weights,
                        "aw": actor_weights,
                        "dw": director_weights,
                        "dcoef": director_weight,
                        "rcoef": rating_weight,
                    },
                },
            }
        }

        resp = await self._es.search(index=self._index, size=limit, query=query)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            dict(h["_source"], **{"_id": h["_id"], "_score": h.get("_score")})
            for h in hits
        ]

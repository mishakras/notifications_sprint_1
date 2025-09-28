from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from recommendation_service.src.db.elastic import get_elastic
from recommendation_service.src.schemas.movies.films import Film
from recommendation_service.src.services.base_service import BaseElasticService


def _as_terms(values: Iterable[str]) -> List[str]:
    return list(set(str(v) for v in values if v))


class FilmService(BaseElasticService[Film]):
    index = "movies"
    model = Film

    async def search_by_ids(self, ids: Iterable[str]) -> List[Film]:
        ids_list = _as_terms(ids)
        if not ids_list:
            return []
        body = {"ids": {"values": ids_list}}
        docs = await self.elastic.mget(index=self.index, body=body)
        result = []
        for d in docs.get("docs", []):
            if d.get("found"):
                src = d.get("_source", {}) or {}
                src["id"] = d.get("_id")
                result.append(self.model(**src))
        return result

    async def search_similar(
        self,
        search_values: Dict[str, Dict[str, float]],
        exclude_ids: Optional[List[str]] = None,
        limit: int = 50,
        director_weight: float = 2.0,
        rating_weight: float = 0.0,
    ) -> List[Film]:
        """
        ЕДИНАЯ методика оценки (и она же в PG — см. comparison_pg_es/pg.py):
        score = SUM( genre_weights[genre_id] )
              + SUM( actor_weights[person_id] )
              + director_weight * SUM( director_weights[person_id] )
              + rating_weight * imdb_rating
        """
        exclude_ids = exclude_ids or []

        genres_w = search_values.get("genres", {})
        actors_w = search_values.get("actors", {})
        directors_w = search_values.get("directors", {})

        should = []
        if genres_w:
            should.append(
                {"nested": {
                    "path": "genres",
                    "query": {"terms": {"genres.id": list(genres_w.keys())}},
                }}
            )
        if actors_w:
            should.append(
                {"nested": {
                    "path": "actors",
                    "query": {"terms": {"actors.id": list(actors_w.keys())}},
                }}
            )
        if directors_w:
            should.append(
                {"nested": {
                    "path": "directors",
                    "query": {"terms": {"directors.id": list(directors_w.keys())}},
                }}
            )

        base_query = {
            "bool": {
                "must_not": [{"ids": {"values": exclude_ids}}] if exclude_ids else [],
                "should": should,
                "minimum_should_match": 1 if should else 0,
            }
        }

        script = """
            double s = 0.0;
            if (!params.genres.isEmpty() && doc.containsKey('genres.id') && !doc['genres.id'].isEmpty()) {
              for (def v : doc['genres.id']) {
                if (params.genres.containsKey(v)) { s += (double)params.genres.get(v); }
              }
            }
            if (!params.actors.isEmpty() && doc.containsKey('actors.id') && !doc['actors.id'].isEmpty()) {
              for (def v : doc['actors.id']) {
                if (params.actors.containsKey(v)) { s += (double)params.actors.get(v); }
              }
            }
            if (!params.directors.isEmpty() && doc.containsKey('directors.id') && !doc['directors.id'].isEmpty()) {
              for (def v : doc['directors.id']) {
                if (params.directors.containsKey(v)) { s += params.director_weight * (double)params.directors.get(v); }
              }
            }
            if (params.rating_weight != 0.0 && doc.containsKey('imdb_rating') && !doc['imdb_rating'].isEmpty()) {
              s += params.rating_weight * (double)doc['imdb_rating'].value;
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
                        "genres": genres_w,
                        "actors": actors_w,
                        "directors": directors_w,
                        "director_weight": director_weight,
                        "rating_weight": rating_weight,
                    },
                },
            }
        }

        resp = await self.elastic.search(
            index=self.index, size=limit, query=query
        )
        hits = resp.get("hits", {}).get("hits", [])
        out = []
        for h in hits:
            src = dict(h.get("_source", {}) or {})
            src["id"] = h.get("_id")
            out.append(self.model(**src))
        return out


def get_film_service() -> FilmService:
    elastic = get_elastic()
    return FilmService(elastic=elastic)

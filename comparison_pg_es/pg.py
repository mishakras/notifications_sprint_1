from __future__ import annotations

import json
from typing import Mapping, Sequence

import asyncpg


class PG:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def __aenter__(self) -> "PG":
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=10)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self._pool is not None
        await self._pool.close()

    async def fetch_by_ids(self, ids: Sequence[str]) -> list[dict]:
        """Вернёт фильмы по списку id, сохранив исходный порядок ids."""
        if not ids:
            return []
        sql = """
            SELECT fw.id, fw.title, fw.rating
            FROM content.film_work AS fw
            WHERE fw.id = ANY($1::uuid[])
            ORDER BY array_position($1::uuid[], fw.id)
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, ids)
        return [dict(r) for r in rows]

    async def rank_by_profile(
        self,
        genre_weights: Mapping[str, float],
        actor_weights: Mapping[str, float],
        director_weights: Mapping[str, float],
        *,
        exclude_ids: Sequence[str] | None = None,
        limit: int = 100,
        director_weight: float = 2.0,
        rating_weight: float = 0.0,
    ) -> list[dict]:
        """
        Считает тот же скор, что и в ES:

        score =
            SUM(genre_w)
          + SUM(actor_w)
          + director_weight * SUM(director_w)
          + rating_weight   * rating
        """
        excluded = exclude_ids if exclude_ids else None

        sql = """
        WITH
        gw AS (
          SELECT (key)::uuid AS id, (value)::float8 AS w
          FROM jsonb_each_text($1::jsonb)
        ),
        aw AS (
          SELECT (key)::uuid AS id, (value)::float8 AS w
          FROM jsonb_each_text($2::jsonb)
        ),
        dw AS (
          SELECT (key)::uuid AS id, (value)::float8 AS w
          FROM jsonb_each_text($3::jsonb)
        ),

        g_acc AS (
          SELECT gfw.film_work_id AS id, SUM(gw.w) AS g_score
          FROM content.genre_film_work AS gfw
          JOIN gw ON gw.id = gfw.genre_id
          GROUP BY gfw.film_work_id
        ),
        a_acc AS (
          SELECT pfw.film_work_id AS id, SUM(aw.w) AS a_score
          FROM content.person_film_work AS pfw
          JOIN aw ON aw.id = pfw.person_id
          WHERE pfw.role = 'actor'
          GROUP BY pfw.film_work_id
        ),
        d_acc AS (
          SELECT pfw.film_work_id AS id, SUM(dw.w) AS d_score
          FROM content.person_film_work AS pfw
          JOIN dw ON dw.id = pfw.person_id
          WHERE pfw.role = 'director'
          GROUP BY pfw.film_work_id
        )

        SELECT
          fw.id,
          fw.title,
          fw.rating,
          COALESCE(g_acc.g_score, 0.0)          AS g_score,
          COALESCE(a_acc.a_score, 0.0)          AS a_score,
          COALESCE(d_acc.d_score, 0.0)          AS d_score,
          ( COALESCE(g_acc.g_score, 0.0)
          + COALESCE(a_acc.a_score, 0.0)
          + $6 * COALESCE(d_acc.d_score, 0.0)
          + $7 * COALESCE(fw.rating, 0.0)
          ) AS score
        FROM content.film_work AS fw
        LEFT JOIN g_acc ON g_acc.id = fw.id
        LEFT JOIN a_acc ON a_acc.id = fw.id
        LEFT JOIN d_acc ON d_acc.id = fw.id
        WHERE ($4::uuid[] IS NULL OR fw.id <> ALL($4::uuid[]))
        ORDER BY score DESC
        LIMIT $5
        """

        params = (
            json.dumps(dict(genre_weights)),
            json.dumps(dict(actor_weights)),
            json.dumps(dict(director_weights)),
            excluded,
            int(limit),
            float(director_weight),
            float(rating_weight),
        )

        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        return [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "rating": r["rating"],
                "g_score": float(r["g_score"]),
                "a_score": float(r["a_score"]),
                "d_score": float(r["d_score"]),
                "score": float(r["score"]),
            }
            for r in rows
        ]

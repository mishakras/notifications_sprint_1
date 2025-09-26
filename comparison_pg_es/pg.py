from __future__ import annotations
import asyncio
import asyncpg
from typing import Sequence
from settings import SETTINGS

class PG:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def __aenter__(self):
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=SETTINGS.concurrent_queries)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._pool:
            await self._pool.close()

    async def fetch_by_ids(self, ids: Sequence[str]) -> list[dict]:
        if not ids:
            return []
        sql = """
            SELECT fw.*
            FROM content.film_work AS fw
            WHERE fw.id = ANY($1::uuid[])
            ORDER BY array_position($1::uuid[], fw.id);
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, list(ids))
        return [dict(r) for r in rows]

    async def rank_by_genres(self, genre_ids: Sequence[str], limit: int = 100, offset: int = 0) -> list[dict]:
        if not genre_ids:
            return []
        sql = """
            WITH input_genres AS (SELECT UNNEST($1::uuid[]) AS genre_id),
            film_match AS (
                SELECT gfw.film_work_id AS film_id, COUNT(*) AS matched_genres
                FROM content.genre_film_work gfw
                JOIN input_genres ig ON ig.genre_id = gfw.genre_id
                GROUP BY gfw.film_work_id
            )
            SELECT fw.*, fm.matched_genres
            FROM film_match fm
            JOIN content.film_work fw ON fw.id = fm.film_id
            ORDER BY fm.matched_genres DESC, fw.rating DESC NULLS LAST, fw.id
            LIMIT $2 OFFSET $3;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, list(genre_ids), limit, offset)
        return [dict(r) for r in rows]

    async def rank_by_persons(self, actor_ids: Sequence[str] | None, director_ids: Sequence[str] | None,
                              limit: int = 100, offset: int = 0,
                              director_weight: int = 2) -> list[dict]:
        actor_ids = list(actor_ids or [])
        director_ids = list(director_ids or [])
        if not actor_ids and not director_ids:
            return []
        sql = """
            WITH
            input_actors AS (SELECT UNNEST($1::uuid[]) AS person_id),
            input_directors AS (SELECT UNNEST($2::uuid[]) AS person_id),
            actor_match AS (
              SELECT pfw.film_work_id AS film_id, COUNT(*)::int AS ca
              FROM content.person_film_work pfw
              JOIN input_actors ia ON ia.person_id = pfw.person_id
              WHERE pfw.role = 'actor'
              GROUP BY pfw.film_work_id
            ),
            director_match AS (
              SELECT pfw.film_work_id AS film_id, COUNT(*)::int AS cd
              FROM content.person_film_work pfw
              JOIN input_directors id ON id.person_id = pfw.person_id
              WHERE pfw.role = 'director'
              GROUP BY pfw.film_work_id
            ),
            merged AS (
              SELECT COALESCE(a.film_id, d.film_id) AS film_id,
                     COALESCE(a.ca, 0) AS ca,
                     COALESCE(d.cd, 0) AS cd
              FROM actor_match a
              FULL JOIN director_match d ON d.film_id = a.film_id
            )
            SELECT fw.*,
                   (m.ca + $3 * m.cd) AS score,
                   m.ca AS matched_actors,
                   m.cd AS matched_directors
            FROM merged m
            JOIN content.film_work fw ON fw.id = m.film_id
            ORDER BY score DESC, fw.rating DESC NULLS LAST, fw.id
            LIMIT $4 OFFSET $5;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, actor_ids, director_ids, director_weight, limit, offset)
        return [dict(r) for r in rows]

async def _demo():
    async with PG(SETTINGS.effective_pg_dsn()) as pg:
        print(await pg.fetch_by_ids([]))

if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())

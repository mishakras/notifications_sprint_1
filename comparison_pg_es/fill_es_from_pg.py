#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncIterator

import asyncpg
from elasticsearch import AsyncElasticsearch

# Этот скрипт намеренно маленький: он НЕ считает и не фильтрует,
# он просто "переливает" фильмы из PG в ES в плоской схеме,
# которая лучше подходит для быстрых terms/filters в ES
# (без nested и без script_score).

PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://postgres:secret@localhost:5432/theatre",
)
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "movies")
BATCH = int(os.getenv("BATCH", "1000"))

CREATE_INDEX_BODY = {
    "mappings": {
        "properties": {
            "rating": {"type": "float"},
            "genre_ids": {"type": "keyword"},
            "actor_ids": {"type": "keyword"},
            "director_ids": {"type": "keyword"},
        },
    },
}

# Берём rating и массива ID (без nested/объектов).
FILMS_SQL = """
SELECT
  fw.id::text AS id,
  COALESCE(fw.rating, 0.0) AS rating,

  COALESCE((
    SELECT array_agg(DISTINCT g.id::text)
    FROM content.genre_film_work gfw
    JOIN content.genre g ON g.id = gfw.genre_id
    WHERE gfw.film_work_id = fw.id
  ), ARRAY[]::text[]) AS genre_ids,

  COALESCE((
    SELECT array_agg(DISTINCT pfw.person_id::text)
    FROM content.person_film_work pfw
    WHERE pfw.film_work_id = fw.id AND pfw.role = 'actor'
  ), ARRAY[]::text[]) AS actor_ids,

  COALESCE((
    SELECT array_agg(DISTINCT pfw.person_id::text)
    FROM content.person_film_work pfw
    WHERE pfw.film_work_id = fw.id AND pfw.role = 'director'
  ), ARRAY[]::text[]) AS director_ids

FROM content.film_work fw
ORDER BY fw.id
"""


async def iter_films(
    conn: asyncpg.Connection,
) -> AsyncIterator[asyncpg.Record]:
    async with conn.transaction():
        async for row in conn.cursor(FILMS_SQL, prefetch=BATCH):
            yield row


def make_doc(row: asyncpg.Record) -> tuple[str, dict[str, Any]]:
    film_id: str = row["id"]
    rating = float(row["rating"] or 0.0)
    # asyncpg для text[] вернёт list[str]
    genre_ids = list(row["genre_ids"] or [])
    actor_ids = list(row["actor_ids"] or [])
    director_ids = list(row["director_ids"] or [])
    doc = {
        "rating": rating,
        "genre_ids": genre_ids,
        "actor_ids": actor_ids,
        "director_ids": director_ids,
    }
    return film_id, doc


async def ensure_index(es: AsyncElasticsearch) -> None:
    exists = await es.indices.exists(index=ES_INDEX)
    if not exists:
        await es.indices.create(index=ES_INDEX, **CREATE_INDEX_BODY)


async def bulk_index(es: AsyncElasticsearch, ops: list[dict]) -> None:
    if not ops:
        return
    resp = await es.bulk(operations=ops, index=ES_INDEX, refresh=False)
    if resp.get("errors"):
        items = resp.get(
            "items",
            [],
        )
        bad = next(
            (it for it in items if list(it.values())[0].get("error")),
            None,
        )
        raise RuntimeError(f"Bulk had errors: {bad}")


async def main() -> None:

    es = AsyncElasticsearch(hosts=[ES_HOST], request_timeout=60)
    try:
        await ensure_index(es)

        pool = await asyncpg.create_pool(PG_DSN, min_size=1, max_size=5)
        try:
            total = 0
            ops: list[dict] = []

            async with pool.acquire() as conn:
                async for row in iter_films(conn):
                    film_id, doc = make_doc(row)
                    ops.append({"index": {"_id": film_id}})
                    ops.append(doc)

                    if len(ops) >= 2 * BATCH:
                        await bulk_index(es, ops)
                        total += BATCH
                        ops.clear()

            if ops:
                await bulk_index(es, ops)
                total += len(ops) // 2
                ops.clear()

            await es.indices.refresh(index=ES_INDEX)
        finally:
            await pool.close()
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(main())

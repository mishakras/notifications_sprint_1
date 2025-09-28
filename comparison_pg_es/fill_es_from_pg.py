#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, AsyncIterator

import asyncpg
from elasticsearch import AsyncElasticsearch


PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:secret@localhost:5432/theatre")
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "movies")
BATCH = int(os.getenv("BATCH", "1000"))


CREATE_INDEX_BODY = {
    "mappings": {
        "properties": {
            "rating": {"type": "float"},
            "genres": {
                "type": "nested",
                "properties": {"id": {"type": "keyword"}},
            },
            "actors": {
                "type": "nested",
                "properties": {"id": {"type": "keyword"}},
            },
            "directors": {
                "type": "nested",
                "properties": {"id": {"type": "keyword"}},
            },
        }
    }
}

# Собираем документ фильма: rating + массивы id для жанров/актёров/режиссёров
FILMS_SQL = """
SELECT
  fw.id::text AS id,
  COALESCE(fw.rating, 0.0) AS rating,

  COALESCE((
    SELECT jsonb_agg(DISTINCT jsonb_build_object('id', g.id::text))
    FROM content.genre_film_work gfw
    JOIN content.genre g ON g.id = gfw.genre_id
    WHERE gfw.film_work_id = fw.id
  ), '[]'::jsonb) AS genres,

  COALESCE((
    SELECT jsonb_agg(DISTINCT jsonb_build_object('id', pfw.person_id::text))
    FROM content.person_film_work pfw
    WHERE pfw.film_work_id = fw.id AND pfw.role = 'actor'
  ), '[]'::jsonb) AS actors,

  COALESCE((
    SELECT jsonb_agg(DISTINCT jsonb_build_object('id', pfw.person_id::text))
    FROM content.person_film_work pfw
    WHERE pfw.film_work_id = fw.id AND pfw.role = 'director'
  ), '[]'::jsonb) AS directors

FROM content.film_work fw
ORDER BY fw.id
"""


async def iter_films(conn: asyncpg.Connection) -> AsyncIterator[asyncpg.Record]:
    # Стримим курсором сразу SQL-строку
    async with conn.transaction():
        async for row in conn.cursor(FILMS_SQL, prefetch=BATCH):
            yield row


def _to_id_list(value: Any) -> list[str]:
    """Нормализует json/jsonb (строкой), list[dict], list[str] → list[str] id."""
    if value is None:
        return []
    # json/jsonb могли прийти как строка
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return []
    result: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                v = item.get("id")
                if v:
                    result.append(str(v))
            elif isinstance(item, str):
                result.append(item)
    return result


def make_doc(row: asyncpg.Record) -> tuple[str, dict[str, Any]]:
    film_id: str = row["id"]
    rating = float(row["rating"] or 0.0)

    genre_ids = _to_id_list(row["genres"])
    actor_ids = _to_id_list(row["actors"])
    director_ids = _to_id_list(row["directors"])

    # Приводим к ожидаемой схеме
    doc = {
        "rating": rating,
        "genres": [{"id": gid} for gid in genre_ids],
        "actors": [{"id": pid} for pid in actor_ids],
        "directors": [{"id": did} for did in director_ids],
    }
    return film_id, doc


async def ensure_index(es: AsyncElasticsearch) -> None:
    exists = await es.indices.exists(index=ES_INDEX)
    if not exists:
        await es.indices.create(index=ES_INDEX, **CREATE_INDEX_BODY)


async def bulk_index(es: AsyncElasticsearch, ops: list[dict]) -> None:
    if not ops:
        return
    # AsyncElasticsearch.bulk ожидает "operations" списком action/doc
    resp = await es.bulk(operations=ops, index=ES_INDEX, refresh=False)
    if resp.get("errors"):
        # Для простоты печатаем первую ошибку
        items = resp.get("items", [])
        bad = next((it for it in items if list(it.values())[0].get("error")), None)
        raise RuntimeError(f"Bulk had errors: {bad}")


async def main() -> None:
    print(f"PG_DSN={PG_DSN}")
    print(f"ES_HOST={ES_HOST}, ES_INDEX={ES_INDEX}")

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
                        print(f"Indexed: {total}+")
                        ops.clear()

            if ops:
                # добиваем хвост
                await bulk_index(es, ops)
                total += len(ops) // 2
                ops.clear()

            await es.indices.refresh(index=ES_INDEX)
            print(f"Done. Indexed total: {total}")
        finally:
            await pool.close()
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(main())

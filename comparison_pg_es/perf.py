from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import statistics as stats
import time
from typing import Sequence

import numpy as np
import pandas as pd
from es import ES
from pg import PG
from settings import SETTINGS
from tabulate import tabulate

LOG = logging.getLogger(__name__)


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(np.percentile(values, 95))


async def bench_once_pg(
    pg: PG,
    ids: Sequence[str],
    genres: Sequence[str],
    actors: Sequence[str],
    directors: Sequence[str],
    limit: int,
) -> tuple[float, float, float]:
    start = time.perf_counter()
    _ = await pg.fetch_by_ids(ids)
    t1 = time.perf_counter()

    _ = await pg.rank_by_genres(genres, limit=limit)
    t2 = time.perf_counter()

    _ = await pg.rank_by_persons(
        actors,
        directors,
        limit=limit,
        director_weight=SETTINGS.director_weight,
    )
    t3 = time.perf_counter()

    return (t1 - start, t2 - t1, t3 - t2)


async def bench_once_es(
    es: ES,
    ids: Sequence[str],
    genres: Sequence[str],
    actors: Sequence[str],
    directors: Sequence[str],
    limit: int,
) -> tuple[float, float, float]:
    start = time.perf_counter()
    _ = await es.fetch_by_ids(ids)
    t1 = time.perf_counter()

    _ = await es.rank_by_genres(genres, limit=limit)
    t2 = time.perf_counter()

    _ = await es.rank_by_persons(
        actors,
        directors,
        limit=limit,
        director_weight=SETTINGS.director_weight,
    )
    t3 = time.perf_counter()

    return (t1 - start, t2 - t1, t3 - t2)


def _choose_inputs(
    base_ids: list[str],
    base_genres: list[str],
    base_actors: list[str],
    base_directors: list[str],
    size: int,
) -> tuple[list[str], list[str], list[str], list[str]]:
    ids = random.sample(base_ids, min(size, len(base_ids)))
    genres = (
        random.sample(base_genres, min(size, len(base_genres)))
        if base_genres
        else []
    )
    actors = (
        random.sample(base_actors, min(size, len(base_actors)))
        if base_actors
        else []
    )
    directors = (
        random.sample(
            base_directors,
            min(max(1, size // 4), len(base_directors)),
        )
        if base_directors
        else []
    )
    return ids, genres, actors, directors


def _build_summary(name: str, values: list[float], size: int) -> dict:
    return {
        "case": name,
        "size": size,
        "count": len(values),
        "avg_ms": round(1000 * stats.mean(values), 2) if values else None,
        "median_ms": (
            round(1000 * stats.median(values), 2) if values else None
        ),
        "p95_ms": round(1000 * p95(values), 2) if values else None,
    }


def _load_bases(
    samples_path: str | None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    if samples_path:
        with open(samples_path, "r", encoding="utf-8") as f:
            samples = json.load(f)
        base_ids = list(samples.get("film_ids", []))
        base_genres = list(samples.get("genre_ids", []))
        base_actors = list(samples.get("actor_ids", []))
        base_directors = list(samples.get("director_ids", []))
        return base_ids, base_genres, base_actors, base_directors

    # избегаем f-строк с форматом {i:012d}, чтобы не ловить E231
    def _tail(number: int) -> str:
        return format(number, "012d")  # эквивалент f"{number:012d}"

    base_ids = [f"00000000-0000-0000-0000-{_tail(i)}" for i in range(1, 5000)]
    base_genres = [
        f"00000000-0000-0000-0000-{_tail(i)}" for i in range(1, 200)
    ]
    base_actors = [
        f"00000000-0000-0000-0000-{_tail(i)}" for i in range(1, 500)
    ]
    base_directors = [
        f"00000000-0000-0000-0000-{_tail(i)}" for i in range(1, 500)
    ]
    return base_ids, base_genres, base_actors, base_directors


async def _warmup(
    pg: PG,
    es: ES,
    bases: tuple[list[str], list[str], list[str], list[str]],
    warmup: int,
    limit: int,
) -> None:
    base_ids, base_genres, base_actors, base_directors = bases
    for _ in range(warmup):
        inputs = _choose_inputs(
            base_ids,
            base_genres,
            base_actors,
            base_directors,
            size=5,
        )
        try:
            await bench_once_pg(pg, *inputs, limit)
        except Exception:
            pass
        try:
            await bench_once_es(es, *inputs, limit)
        except Exception:
            pass


async def _measure(
    pg: PG,
    es: ES,
    bases: tuple[list[str], list[str], list[str], list[str]],
    size_list: list[int],
    iterations: int,
    limit: int,
) -> list[dict]:
    base_ids, base_genres, base_actors, base_directors = bases
    rows: list[dict] = []
    for size in size_list:
        pg_fetch: list[float] = []
        pg_rg: list[float] = []
        pg_rp: list[float] = []

        es_fetch: list[float] = []
        es_rg: list[float] = []
        es_rp: list[float] = []

        for _ in range(iterations):
            inputs = _choose_inputs(
                base_ids,
                base_genres,
                base_actors,
                base_directors,
                size=size,
            )
            try:
                t_fetch, t_rg, t_rp = await bench_once_pg(pg, *inputs, limit)
                pg_fetch.append(t_fetch)
                pg_rg.append(t_rg)
                pg_rp.append(t_rp)
            except Exception:
                pass
            try:
                t_fetch, t_rg, t_rp = await bench_once_es(es, *inputs, limit)
                es_fetch.append(t_fetch)
                es_rg.append(t_rg)
                es_rp.append(t_rp)
            except Exception:
                pass

        rows.extend(
            [
                _build_summary("PG fetch_by_ids", pg_fetch, size),
                _build_summary("PG rank_by_genres", pg_rg, size),
                _build_summary("PG rank_by_persons", pg_rp, size),
                _build_summary("ES fetch_by_ids", es_fetch, size),
                _build_summary("ES rank_by_genres", es_rg, size),
                _build_summary("ES rank_by_persons", es_rp, size),
            ],
        )
    return rows


async def run(
    size_list: list[int],
    iterations: int,
    warmup: int,
    limit: int,
    samples_path: str | None,
) -> None:
    bases = _load_bases(samples_path)
    async with PG(SETTINGS.effective_pg_dsn()) as pg, ES(
        SETTINGS.es_host,
        SETTINGS.es_index,
    ) as es:
        await _warmup(pg, es, bases, warmup, limit)
        rows = await _measure(pg, es, bases, size_list, iterations, limit)

    df = pd.DataFrame(rows)
    df.to_csv("benchmark_results.csv", index=False)

    table_text = tabulate(
        df,
        headers="keys",
        tablefmt="github",
        showindex=False,
    )
    LOG.info("\n%s", table_text)
    LOG.info("Saved: benchmark_results.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sizes",
        type=str,
        default="5,20,100",
        help="Список размеров входных ID (через запятую).",
    )
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--use-samples",
        type=str,
        default=None,
        help="Путь к samples.json (из prepare_samples.py).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ARGS = parse_args()
    SIZES = [int(x.strip()) for x in ARGS.sizes.split(",") if x.strip()]
    asyncio.run(
        run(
            SIZES,
            ARGS.iterations,
            ARGS.warmup,
            ARGS.limit,
            ARGS.use_samples,
        ),
    )

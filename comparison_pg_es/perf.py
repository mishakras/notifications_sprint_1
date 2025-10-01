from __future__ import annotations

import argparse
import asyncio
import random
import statistics as stats
import time
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
from es import ES
from pg import PG
from settings import SETTINGS


def p95(values: List[float]) -> float:
    return float(np.percentile(values, 95)) if values else 0.0


def _mk_weights(ids: Sequence[str]) -> Dict[str, float]:
    # имитируем историю: случайный
    # watched_percentage in [0.5, 1.0] w = (p * 3.5 - 1.5)
    out: Dict[str, float] = {}
    for i in ids:
        percent = random.uniform(0.5, 1.0)
        out[str(i)] = (percent * 3.5) - 1.5
    return out


async def bench_once(
    pg: PG,
    es: ES,
    size: int,
    limit: int,
) -> Dict[str, float]:
    # синтетические "базы" id (UUID-вид)
    persons = [
        f"00000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(1, 1000)
    ]
    genres = [
        f"00000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(1, 300)
    ]

    pick_genres = random.sample(genres, min(size, len(genres)))
    pick_actors = random.sample(persons, min(size, len(persons)))
    pick_directors = random.sample(
        persons,
        min(max(1, size // 4), len(persons)),
    )

    gw = _mk_weights(pick_genres)
    aw = _mk_weights(pick_actors)
    dw = _mk_weights(pick_directors)

    t0 = time.perf_counter()
    await pg.rank_by_profile(
        gw,
        aw,
        dw,
        limit=limit,
        director_weight=SETTINGS.director_weight,
    )
    t1 = time.perf_counter()
    await es.rank_by_profile(
        gw,
        aw,
        dw,
        limit=limit,
        director_weight=SETTINGS.director_weight,
    )
    t2 = time.perf_counter()

    return {"PG": t1 - t0, "ES": t2 - t1}


async def run(
    sizes: List[int],
    iterations: int,
    warmup: int,
    limit: int,
) -> None:
    rows = []

    async with (
        PG(SETTINGS.effective_pg_dsn()) as pg,
        ES(SETTINGS.es_host, SETTINGS.es_index) as es,
    ):
        # warmup
        for _ in range(warmup):
            await bench_once(pg, es, size=5, limit=limit)

        for size in sizes:
            pg_times, es_times = [], []
            for _ in range(iterations):
                bench = await bench_once(pg, es, size=size, limit=limit)
                pg_times.append(bench["PG"])
                es_times.append(bench["ES"])

            def row(name: str, size: int, arr: List[float]) -> dict:
                return {
                    "case": name,
                    "size": size,
                    "count": len(arr),
                    "avg_ms": (
                        round(1000 * stats.mean(arr), 2) if arr else None,
                    ),
                    "median_ms": (
                        round(1000 * stats.median(arr), 2) if arr else None,
                    ),
                    "p95_ms": round(1000 * p95(arr), 2) if arr else None,
                }

            rows.extend(
                [
                    row("PG rank_by_profile", size, pg_times),
                    row("ES rank_by_profile", size, es_times),
                ],
            )

    df = pd.DataFrame(rows)
    df.to_csv("benchmark_results.csv", index=False)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=str, default="5,20,100")
    ap.add_argument("--iterations", type=int, default=10)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--limit", type=int, default=100)
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sizes = [int(x.strip()) for x in args.sizes.split(",") if x.strip()]
    asyncio.run(run(sizes, args.iterations, args.warmup, args.limit))

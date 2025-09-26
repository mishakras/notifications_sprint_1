from __future__ import annotations
import asyncio, random, time, statistics as stats, argparse, json
from typing import Sequence
import numpy as np, pandas as pd
from tabulate import tabulate
from settings import SETTINGS
from pg import PG
from es import ES

def p95(values: list[float]) -> float:
    return float(np.percentile(values, 95)) if values else 0.0

async def bench_once_pg(pg: PG, ids: Sequence[str], genres: Sequence[str], actors: Sequence[str], directors: Sequence[str], limit: int):
    t0=time.perf_counter(); _=await pg.fetch_by_ids(ids); t1=time.perf_counter()
    _=await pg.rank_by_genres(genres, limit=limit); t2=time.perf_counter()
    _=await pg.rank_by_persons(actors, directors, limit=limit, director_weight=SETTINGS.director_weight); t3=time.perf_counter()
    return (t1-t0, t2-t1, t3-t2)

async def bench_once_es(es: ES, ids: Sequence[str], genres: Sequence[str], actors: Sequence[str], directors: Sequence[str], limit: int):
    t0=time.perf_counter(); _=await es.fetch_by_ids(ids); t1=time.perf_counter()
    _=await es.rank_by_genres(genres, limit=limit); t2=time.perf_counter()
    _=await es.rank_by_persons(actors, directors, limit=limit, director_weight=SETTINGS.director_weight); t3=time.perf_counter()
    return (t1-t0, t2-t1, t3-t2)

async def run(size_list: list[int], iterations: int, warmup: int, limit: int, samples_path: str | None):
    # --- источники ID ---
    if samples_path:
        with open(samples_path, "r", encoding="utf-8") as f:
            samples = json.load(f)
        base_ids     = list(samples.get("film_ids", []))      or [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 5000)]
        base_genres  = list(samples.get("genre_ids", []))     or [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 200)]
        base_actors  = list(samples.get("actor_ids", []))     or [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 500)]
        base_directs = list(samples.get("director_ids", []))  or [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 500)]
    else:
        base_ids     = [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 5000)]
        base_genres  = [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 200)]
        base_actors  = [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 500)]
        base_directs = [f"00000000-0000-0000-0000-{i:012d}" for i in range(1, 500)]

    async with PG(SETTINGS.effective_pg_dsn()) as pg, ES(SETTINGS.es_host, SETTINGS.es_index) as es:
        # warmup
        for _ in range(warmup):
            ids       = random.sample(base_ids,    min(5, len(base_ids)))
            genres    = random.sample(base_genres, min(5, len(base_genres)))
            actors    = random.sample(base_actors, min(5, len(base_actors)))
            directors = random.sample(base_directs, min(3, len(base_directs)))
            try: await bench_once_pg(pg, ids, genres, actors, directors, limit)
            except Exception: pass
            try: await bench_once_es(es, ids, genres, actors, directors, limit)
            except Exception: pass

        rows=[]
        for size in size_list:
            pg_fetch=pg_rg=pg_rp=es_fetch=es_rg=es_rp=[]; pg_fetch,pg_rg,pg_rp,es_fetch,es_rg,es_rp = [],[],[],[],[],[]
            for _ in range(iterations):
                if len(base_ids)==0: break
                ids       = random.sample(base_ids,    min(size, len(base_ids)))
                genres    = random.sample(base_genres, min(size, len(base_genres))) if base_genres else []
                actors    = random.sample(base_actors, min(size, len(base_actors))) if base_actors else []
                directors = random.sample(base_directs, min(max(1, size//4), len(base_directs))) if base_directs else []

                try:
                    a,b,c = await bench_once_pg(pg, ids, genres, actors, directors, limit)
                    pg_fetch.append(a); pg_rg.append(b); pg_rp.append(c)
                except Exception: pass

                try:
                    a,b,c = await bench_once_es(es, ids, genres, actors, directors, limit)
                    es_fetch.append(a); es_rg.append(b); es_rp.append(c)
                except Exception: pass

            def summary(name:str, arr:list[float]):
                return {"case":name,"size":size,"count":len(arr),
                        "avg_ms":round(1000*stats.mean(arr),2) if arr else None,
                        "median_ms":round(1000*stats.median(arr),2) if arr else None,
                        "p95_ms":round(1000*p95(arr),2) if arr else None}
            rows.extend([
                summary("PG fetch_by_ids",pg_fetch),
                summary("PG rank_by_genres",pg_rg),
                summary("PG rank_by_persons",pg_rp),
                summary("ES fetch_by_ids",es_fetch),
                summary("ES rank_by_genres",es_rg),
                summary("ES rank_by_persons",es_rp),
            ])

    pd.DataFrame(rows).to_csv("benchmark_results.csv", index=False)
    print(tabulate(pd.DataFrame(rows), headers="keys", tablefmt="github", showindex=False))
    print("\nSaved: benchmark_results.csv")

def parse_args():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sizes", type=str, default="5,20,100")
    ap.add_argument("--iterations", type=int, default=10)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--use-samples", type=str, default=None, help="Путь к samples.json (из prepare_samples.py)")
    return ap.parse_args()

if __name__=="__main__":
    args=parse_args()
    sizes=[int(x.strip()) for x in args.sizes.split(",") if x.strip()]
    asyncio.run(run(sizes, args.iterations, args.warmup, args.limit, args.use_samples))

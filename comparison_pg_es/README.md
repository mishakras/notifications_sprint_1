# PG vs ES Benchmark (Project-Fitted)

В тесте применяется:
- PostgreSQL: схема `content` и таблицы `film_work`, `genre_film_work`, `person_film_work`.
- Elasticsearch: индекс `movies` c nested: `genres`, `actors`, `directors` (ID лежат в `*.id`).

## Запуск
```bash
pip install -r requirements.txt
python perf.py --sizes 5,20,100 --iterations 10 --warmup 2 --limit 100
```
Результаты: `benchmark_results.csv`.

| case               |   size |   count |   avg_ms |   median_ms |   p95_ms |
|--------------------|--------|---------|----------|-------------|----------|
| PG rank_by_profile |      5 |      10 |     9.9  |       10.24 |    11.21 |
| ES rank_by_profile |      5 |      10 |    10.38 |       10.58 |    11.74 |
| PG rank_by_profile |     20 |      10 |     7.44 |        6.72 |    10.64 |
| ES rank_by_profile |     20 |      10 |     8.52 |        8.17 |    11.96 |
| PG rank_by_profile |    100 |      10 |     8.15 |        7.86 |    11.07 |
| ES rank_by_profile |    100 |      10 |    12.96 |        9.74 |    29.23 |



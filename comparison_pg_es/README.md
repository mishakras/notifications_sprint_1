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
| PG rank_by_profile |      5 |      10 |    10.57 |       10.24 |    11.68 |
| ES rank_by_profile |      5 |      10 |     9.34 |        9.39 |     9.76 |
| PG rank_by_profile |     20 |      10 |     8.97 |       10.17 |    10.67 |
| ES rank_by_profile |     20 |      10 |     8.48 |        8.85 |    10.87 |
| PG rank_by_profile |    100 |      10 |    11.04 |       11.64 |    12.97 |
| ES rank_by_profile |    100 |      10 |    12.22 |       12.31 |    13.38 |



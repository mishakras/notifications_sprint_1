from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from elasticsearch import AsyncElasticsearch


class ES:
    def __init__(
        self,
        host: str,
        index: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        basic_auth = (user, password) if user and password else None
        self._es = AsyncElasticsearch(
            hosts=[host],
            basic_auth=basic_auth,
            request_timeout=30,
        )
        self._index = index

    async def __aenter__(self) -> "ES":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._es.close()

    async def close(self) -> None:
        await self._es.close()

    # ------------ helpers ------------

    @staticmethod
    def _topk_items(
            weights: Dict[str, float],
            key: int,
    ) -> List[Tuple[str, float]]:
        """Берём по модулю веса — самые «влияющие»."""
        return sorted(
            weights.items(),
            key=lambda kv: abs(kv[1]),
            reverse=True,
        )[:key]

    # ------------ основной метод сравнения ------------

    async def rank_by_profile(
        self,
        genre_weights: Dict[str, float],
        actor_weights: Dict[str, float],
        director_weights: Dict[str, float],
        *,
        exclude_ids: Sequence[str] | None = None,
        limit: int = 100,
        director_weight: float = 2.0,
        rating_weight: float = 0.0,
        top_k: int = 256,
    ) -> list[dict]:
        """
        [Design note] Сравнение с PG без скриптов:
        - используем function_score + term/terms по ПЛОСКИМ полям *_ids
         (см. fill_es_from_pg.py), без painless;
        - rating добавляем через field_value_factor;
        - итоговая формула 1-в-1 с PG:
          sum(genres) + sum(actors) + director_weight * sum(directors)
           + rating_weight * rating;
        - ограничиваем число функций через top_k, чтобы не раздувать запрос;
        - отказ от nested выбран намеренно: для этого кейса плоская
         схема дешевле по исполнению.
        Примечание: на маленьком датасете
        ES может быть медленнее из-за оверхеда координации;
        на больших объёмах выигрывает за счёт инвертированных индексов и кэшей.
        """
        exclude_ids = list(exclude_ids or [])

        # умножаем веса режиссёров на коэффициент
        dir_w = {
            key: float(val) * float(director_weight)
            for key, val in (director_weights or {}).items()
        }

        # ограничиваем количество функций, чтобы не раздувать запрос
        g_top = self._topk_items(genre_weights or {}, top_k)
        a_top = self._topk_items(actor_weights or {}, top_k)
        d_top = self._topk_items(dir_w or {}, top_k)

        functions: List[dict] = []
        should: List[dict] = []

        # функции-веса на совпадения ID (плоские поля, без nested)
        for pid, weight in g_top:
            functions.append(
                {
                    "filter": {
                        "term": {
                            "genre_ids": pid,
                        }
                    },
                    "weight": float(weight),
                },
            )
        for pid, weight in a_top:
            functions.append(
                {
                    "filter": {
                            "term": {
                                "actor_ids": pid,
                            }
                        },
                    "weight": float(weight),
                },
            )
        for pid, weight in d_top:
            functions.append(
                {
                    "filter": {
                        "term": {
                            "director_ids": pid,
                        }
                    },
                    "weight": float(weight),
                },
            )

        # вклад рейтинга через field_value_factor
        if rating_weight and float(rating_weight) != 0.0:
            functions.append(
                {
                    "field_value_factor": {
                        "field": "rating",
                        "factor": float(rating_weight),
                        "missing": 0.0,
                    },
                },
            )

        # базовый запрос — нужен хотя бы один матч по профилю
        if g_top:
            should.append({"terms": {"genre_ids": [pid for pid, _ in g_top]}})
        if a_top:
            should.append({"terms": {"actor_ids": [pid for pid, _ in a_top]}})
        if d_top:
            should.append(
                {
                    "terms": {
                        "director_ids": [pid for pid, _ in d_top]
                    },
                },
            )

        if should:
            base_query: dict = {
                "bool": {
                    "should": should,
                    "minimum_should_match": 1,
                },
            }
        else:
            # если профиль пуст — матчим всё (останется только рейтинг)
            base_query = {"match_all": {}}

        if exclude_ids:
            base_query = {
                "bool": {
                    "must": [base_query],
                    "must_not": [{"ids": {"values": exclude_ids}}],
                },
            }

        q = {
            "function_score": {
                "query": base_query,
                "functions": functions,
                "score_mode": "sum",
                "boost_mode": "sum",
            },
        }

        resp = await self._es.search(index=self._index, size=limit, query=q)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            dict(h["_source"], **{"_id": h["_id"], "_score": h.get("_score")})
            for h in hits
        ]

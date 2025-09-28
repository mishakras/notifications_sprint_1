from __future__ import annotations

from typing import Dict, Iterable

from recommendation_service.src.services.completion.video_completion import (
    VideoCompletionService,
    get_video_completion_service,
)
from recommendation_service.src.services.movies.films import (
    FilmService,
    get_film_service,
)


def _weight_from_watch_percent(p: float) -> float:
    # точная формула из вашего комментария:
    # 1 * (watched_percentage * 3.5 - 1.5)
    return (p * 3.5) - 1.5


class RecommendationService:
    def __init__(
        self,
        completion_service: VideoCompletionService,
        films_service: FilmService,
    ) -> None:
        self.completion_service = completion_service
        self.films_service = films_service

    async def get_recommendations(
        self,
        user_id: str,
        search_values: Dict[str, Dict[str, float]],
        limit: int = 50,
    ):
        """
        search_values — словарь вида:
        {
          "genres": { "<genre_id>": weight, ... },
          "actors": { "<person_id>": weight, ... },
          "directors": { "<person_id>": weight, ... }
        }
        Мы ДОБАВЛЯЕМ сюда веса из истории просмотров.
        """
        history = await self.get_history(user_id)
        if not history:
            # без истории — вернём просто популярное (или пусто)
            return await self.films_service.search_similar(
                search_values=search_values,
                exclude_ids=[],
                limit=limit,
            )

        # film_id -> watched_percentage
        ids_to_pct = {
            h.film_id: float(h.watched_percentage) for h in history
        }

        # подгружаем фильмы из истории, чтобы вытащить их жанры/актеров/режиссёров
        films = await self.films_service.search_by_ids(list(ids_to_pct.keys()))
        if not films:
            return []

        # накапливаем веса в search_values по формуле
        for film in films:
            p = ids_to_pct.get(film.id, 0.0)
            w = _weight_from_watch_percent(p)

            def _accumulate(bucket: Dict[str, float], ids: Iterable[str]):
                for _id in ids:
                    bucket[_id] = bucket.get(_id, 0.0) + w

            _accumulate(search_values.setdefault("genres", {}), [g.id for g in film.genres])
            _accumulate(search_values.setdefault("actors", {}), [a.id for a in film.actors])
            _accumulate(search_values.setdefault("directors", {}), [d.id for d in film.directors])

        # исключаем из выдачи уже просмотренные
        return await self.films_service.search_similar(
            search_values=search_values,
            exclude_ids=list(ids_to_pct.keys()),
            limit=limit,
        )

    async def get_history(self, user_id):
        return await self.completion_service.get_list(
            {
                "user_id": {"comparison": "=", "value": user_id},
                "watched_percentage": {"comparison": ">=", "value": 0.5},
            }
        )


recommendation_service = RecommendationService(
    completion_service=get_video_completion_service(),
    films_service=get_film_service(),
)


def get_recommendation_service() -> RecommendationService:
    yield recommendation_service

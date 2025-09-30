from recommendation.src.services.completion.video_completion import (
    VideoCompletionService,
    get_video_completion_service,
)
from recommendation.src.services.movies.films import (
    FilmService,
    get_film_service,
)


class RecommendationService:

    def __init__(
        self,
        completion_service: VideoCompletionService,
        films_service: FilmService,
    ):
        self.completion_service = completion_service
        self.films_service = films_service

    async def get_recommendations(
        self,
        user_id: str,
        search_values: dict[str:dict],
    ):
        films_history = await self.get_history(user_id)
        if len(films_history):
            films_ids_to_percentage = {
                history.film_id: films_history.watched_percentage
                for history in films_history
            }
            films = await self.films_service.search_by_ids(
                films_ids_to_percentage.keys(),
            )
            for film in films:
                for field in search_values.keys():
                    search_values[field] = self.add_elements_to_search_fields(
                        search_values[field],
                        film[field],
                        films_ids_to_percentage[film.id],
                    )
            return await self.films_service.search_similar(
                search_values,
                list(films_ids_to_percentage.keys()),
            )

    async def get_history(self, user_id):
        films_history = await self.completion_service.get_list({
            "user_id": {
                "comparison": "=",
                "value": user_id,
            },
            "watched_percentage": {
                "comparison": ">=",
                "value": 0.5,
            },
        })
        return films_history

    def add_elements_to_search_fields(
            self,
            search_values,
            film_field,
            watched_percentage,
    ):
        for element in film_field:
            if search_values.get(
                    element.id,
                    None,
            ) is None:
                search_values[element.id] = 1*(watched_percentage * 3.5 - 1.5)
            else:
                search_values[element.id] += 1*(watched_percentage * 3.5 - 1.5)
        return search_values


recommendation_service = RecommendationService(
    completion_service=get_video_completion_service(),
    films_service=get_film_service(),
)


def get_recommendation_service() -> RecommendationService:
    yield recommendation_service

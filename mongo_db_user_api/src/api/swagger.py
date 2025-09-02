# Film_marks

film_mark_detail_schema = {
    "summary": "Получить детальную информацию о закладке",
    "description": "Возвращает полные данные о закладке по ее UUID",
    "response_description": "Детальная информация о закладке",
    "responses": {
        404: {
            "description": "Mark not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Mark not found",
                    },
                },
            },
        },
    },
}

film_mark_create_schema = {
    "summary": "Создать закладку",
    "description": "Создает закладку по UUID пользователя и UUID фильма",
    "response_description": "Детальная информация о созданной закладке",
}

film_mark_delete_schema = {
    "summary": "Удалить закладку",
    "description": "Удаляет закладку по ее UUID",
}

film_mark_search_schema = {
    "summary": "Поиск закладок",
    "description": (
        "Поиск закладок по запросу с пагинацией и фильтрацией по пользователям"
    ),
    "response_description": "Список найденных закладок",
}

# Film_scores

film_score_detail_schema = {
    "summary": "Получить детальную информацию об оценке фильма",
    "description": "Возвращает полные данные об оценке фильма по ее UUID",
    "response_description": "Детальная информация об оценке фильма",
    "responses": {
        404: {
            "description": "Score not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Score not found",
                    },
                },
            },
        },
    },
}

film_score_create_schema = {
    "summary": "Создать оценку фильма",
    "description": "Создает оценку фильма по UUID"
    " пользователя, UUID фильма и значению оценки",
    "response_description": "Детальная информация о созданной оценке",
}

film_score_delete_schema = {
    "summary": "Удалить оценку",
    "description": "Удаляет оценку по ее UUID",
}

film_score_search_schema = {
    "summary": "Поиск оценок",
    "description": (
        "Поиск оценок по запросу с пагинацией"
        " и фильтрацией по пользователям и фильмам"
    ),
    "response_description": "Список найденных оценок",
}

# reviews

review_detail_schema = {
    "summary": "Получить детальную информацию об рецензии фильма",
    "description": "Возвращает полные данные об рецензии фильма по ее UUID",
    "response_description": "Детальная информация об рецензии фильма",
    "responses": {
        404: {
            "description": "Review not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Review not found",
                    },
                },
            },
        },
    },
}

review_create_schema = {
    "summary": "Создать рецензию о фильме",
    "description": "Создает рецензию о фильме"
    " по UUID пользователя, UUID фильма,"
    " тексту рецензии и опционально оценке",
    "response_description": "Детальная информация о созданной рецензии",
}

review_delete_schema = {
    "summary": "Удалить рецензию",
    "description": "Удаляет рецензию по ее UUID",
}

review_search_schema = {
    "summary": "Поиск рецензий",
    "description": (
        "Поиск рецензий по запросу с пагинацией"
        " и фильтрацией по пользователям и фильмам"
    ),
    "response_description": "Список найденных рецензий",
}

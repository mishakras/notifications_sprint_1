# Films

film_detail_schema = {
    "summary": "Получить детальную информацию о фильме",
    "description": "Возвращает полные данные о фильме по его UUID",
    "response_description": "Детальная информация о фильме",
    "responses": {
        404: {
            "description": "Film not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Film not found",
                    },
                },
            },
        },
    },
}


film_search_schema = {
    "summary": "Поиск фильмов",
    "description": (
        "Поиск фильмов по запросу с пагинацией и фильтрацией по меткам"
    ),
    "response_description": "Список найденных фильмов",
}


films_listing_schema = {
    "summary": "Список фильмов",
    "description": (
        "Получение списка фильмов с пагинацией и фильтрацией по жанру"
    ),
    "response_description": "Список фильмов",
}

# Genres

genre_detail_schema = {
    "summary": "Получить информацию о жанре",
    "description": "Возвращает данные о жанре по его UUID",
    "response_description": "Информация о жанре",
    "responses": {
        404: {
            "description": "Genre not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Genre not found",
                    },
                },
            },
        },
    },
}

genre_search_schema = {
    "summary": "Поиск жанров",
    "description": "Поиск жанров по запросу с пагинацией",
    "response_description": "Список найденных жанров",
}


genres_listing_schema = {
    "summary": "Список жанров",
    "description": "Получение списка жанров с пагинацией",
    "response_description": "Список жанров",
}

# Persons

person_detail_schema = {
    "summary": "Получить информацию о персоне",
    "description": "Возвращает данные о персоне по его UUID",
    "response_description": "Информация о персоне",
    "responses": {
        404: {
            "description": "Person not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Person not found",
                    },
                },
            },
        },
    },
}


person_search_schema = {
    "summary": "Поиск персон",
    "description": "Поиск персон по запросу с пагинацией",
    "response_description": "Список найденных персон",
}


persons_listing_schema = {
    "summary": "Список персон",
    "description": "Получение списка персон с пагинацией",
    "response_description": "Список персон",
}


films_by_person_schema = {
    "summary": "Получить фильмы персоны",
    "description": (
        "Возвращает список фильмов, связанных с персоной по её UUID"
    ),
    "response_description": "Список фильмов персоны",
    "responses": {
        404: {
            "description": "Films not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Films not found"},
                },
            },
        },
    },
}

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    es_host: str = Field("http://elastic:9200")
    model_config = ConfigDict(
        json_schema_extra={
            "properties": {
                "es_host": {
                    "example": "http://elastic:9200",
                },
                "env_prefix": "",
                "env_mapping": {
                    "es_host": "ELASTIC_HOST",
                },
            },
        },
    )
    es_id_field: str = "id"
    es_movies_index: str = "movies"
    es_movies_index_mapping: dict = {
        "settings": {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {
                        "type": "stop",
                        "stopwords": "_english_",
                    },
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english",
                    },
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english",
                    },
                    "russian_stop": {
                        "type": "stop",
                        "stopwords": "_russian_",
                    },
                    "russian_stemmer": {
                        "type": "stemmer",
                        "language": "russian",
                    },
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    },
                },
            },
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {
                    "type": "keyword",
                },
                "imdb_rating": {
                    "type": "float",
                },
                "genres": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {
                            "type": "keyword",
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "ru_en",
                        },
                    },
                },
                "title": {
                    "type": "text",
                    "analyzer": "ru_en",
                    "fields": {
                        "raw": {
                            "type": "keyword",
                        },
                    },
                },
                "description": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
                "labels": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
                "directors_names": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
                "actors_names": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
                "writers_names": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
                "directors": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {
                            "type": "keyword",
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "ru_en",
                        },
                    },
                },
                "actors": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {
                            "type": "keyword",
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "ru_en",
                        },
                    },
                },
                "writers": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {
                            "type": "keyword",
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "ru_en",
                        },
                    },
                },
            },
        },
    }
    es_persons_index: str = "persons"
    es_persons_index_mapping: dict = {
        "settings": {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {
                        "type": "stop",
                        "stopwords": "_english_",
                    },
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english",
                    },
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english",
                    },
                    "russian_stop": {
                        "type": "stop",
                        "stopwords": "_russian_",
                    },
                    "russian_stemmer": {
                        "type": "stemmer",
                        "language": "russian",
                    },
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    },
                },
            },
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {
                    "type": "keyword",
                },
                "name": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
            },
        },
    }
    es_genres_index: str = "genres"
    es_genres_index_mapping: dict = {
        "settings": {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {
                        "type": "stop",
                        "stopwords": "_english_",
                    },
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english",
                    },
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english",
                    },
                    "russian_stop": {
                        "type": "stop",
                        "stopwords": "_russian_",
                    },
                    "russian_stemmer": {
                        "type": "stemmer",
                        "language": "russian",
                    },
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    },
                },
            },
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "id": {
                    "type": "keyword",
                },
                "name": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
                "description": {
                    "type": "text",
                    "analyzer": "ru_en",
                },
            },
        },
    }

    redis_host: str = "redis"
    service_url: str = "http://nginx"
    testdata_dir: str = "tests/testdata"
    film_api_url: str = "/api/v1/films/"


test_settings = TestSettings()

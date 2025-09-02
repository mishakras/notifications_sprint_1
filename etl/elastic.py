import json
import logging
import random
from datetime import datetime
from typing import Any, Dict, NoReturn

import elasticsearch
from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch, helpers
from elasticsearch import logger as es_logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt

es_logger.setLevel(logging.WARNING)


class ElasticSupport:
    def __init__(self, config: Dict[str, Any]) -> NoReturn:
        self.config = config
        self.schema_exists = None
        self.elastic_host = "http://%s:%s" % (
            self.config["ELASTIC_HOST"],
            self.config["ELASTIC_PORT"],
        )
        self.es = Elasticsearch([self.elastic_host])
        self.current_year = datetime.now().year

    @retry(
        stop=stop_after_attempt(1),
        retry=retry_if_exception_type(elasticsearch.NotFoundError),
    )
    def movies_index_check_or_create(self) -> NoReturn:
        try:
            movies_index = self.get_index("movies")
            logging.info(movies_index)
        except elasticsearch.NotFoundError:
            for index_name, schema_file in self.config[
                "INDEX_JSON_FILES"
            ].items():
                self.create_index(
                    index_name,
                    self.load_index_schemas(schema_file),
                )
            self.schema_exists = True

    def is_movies_new(self, creation_date) -> bool:
        return (self.current_year - creation_date) < 4

    def get_index(self, index: str) -> ObjectApiResponse[Any]:
        return self.es.indices.get_alias(index=index)

    def create_index(
        self,
        index_name: str,
        index_schema: Dict[str, Any],
    ) -> NoReturn:
        self.es.indices.create(
            index=index_name,
            body=index_schema,
        )

    def load_index_schemas(self, schema_file: str) -> Dict[str, Any]:
        with open(schema_file) as json_file:
            json_data = json.load(json_file)
        return json_data

    def prepare_movie_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for movie in data:
            creation_date = random.randint(1950, 2024)
            movie["labels"] = []
            if self.is_movies_new(creation_date):
                movie["labels"].append("is_new")
            movie["directors"] = []
            movie["actors"] = []
            movie["writers"] = []
            movie["directors_names"] = []
            movie["actors_names"] = []
            movie["writers_names"] = []
            persons = movie.pop("persons")
            for person in persons:
                person["id"] = person.pop("person_id")
                person["name"] = person.pop("person_name")
                role = person.pop("person_role")
                for job_title in ["directors", "actors", "writers"]:
                    if role in job_title:
                        movie[job_title].append(person)
                        for agg_job_title in [
                            "directors_names",
                            "actors_names",
                            "writers_names",
                        ]:
                            if role in agg_job_title:
                                movie[agg_job_title].append(person["name"])
        return data

    def upload_data(self, data: Dict[str, Any], source: str) -> NoReturn:
        final_data = data
        match source:
            case "movies":
                final_data = self.prepare_movie_data(data)
        actions = [
            {
                "_index": source,
                "_source": item,
                "_id": item["id"],
            }
            for item in final_data
        ]
        helpers.bulk(self.es, actions)

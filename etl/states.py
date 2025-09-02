import itertools
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, Generator, NoReturn, Union

import psycopg
from postgres import PostgresExtractor
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)


class LocalStateStorage:
    def __init__(self, file_path: str) -> NoReturn:
        self.file_path = file_path

    def save_state(self, state: str) -> NoReturn:
        with open(self.file_path, "wt") as storage:
            storage.write(state.strftime("%m-%d-%Y %H:%M:%S"))

    def retrieve_state(self) -> Union[str, None]:
        try:
            with open(self.file_path, "r") as storage:
                try:
                    state = storage.read()
                except:
                    return None
            return datetime.strptime(state, "%m-%d-%Y %H:%M:%S")
        except FileNotFoundError:
            with open(self.file_path, "w") as storage:
                storage.write("01-01-1970 00:00:00")
            return None


class DataProcessing:
    def __init__(self, config: Dict[str, Any]) -> NoReturn:
        self.last_modified = config["DEFAULT_MODIFIED"]
        self.config = config
        self.local_storage = LocalStateStorage(
            self.config["STORAGE_JSON_FILE"],
        )
        self.dsl = {
            "dbname": self.config["POSTGRES_DB"],
            "user": self.config["POSTGRES_USER"],
            "password": self.config["POSTGRES_PASSWORD"],
            "host": self.config["DB_HOST"],
            "port": self.config["DB_PORT"],
        }

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=30),
        stop=stop_after_delay(60),
        retry=retry_if_exception_type(psycopg.OperationalError),
    )
    def retrieve_postgres_data(self, source: str) -> Generator:
        modified_time = self.retrieve_actual_state()
        pg_client = PostgresExtractor(self.dsl, self.config, modified_time)
        match source:
            case "movies":
                raw_query = pg_client.movies_query()
            case "genres":
                raw_query = pg_client.genres_query()
            case "persons":
                raw_query = pg_client.persons_query()
        with closing(pg_client.connect()):
            for data in pg_client.retrieve_data(raw_query, source):
                yield data

    def retrieve_actual_state(self) -> str:
        return self.local_storage.retrieve_state() or self.last_modified

    def save_actual_state(self, last_modified_time: str) -> NoReturn:
        self.local_storage.save_state(last_modified_time)

    def actualize_current_state(
        self,
        item: Dict[str, Any],
        source: str,
    ) -> NoReturn:
        last_modified_time = self.config["DEFAULT_MODIFIED"]
        last_modified_time_data = item.pop("modified")
        match source:
            case "movies":
                last_modified_time_genres = item.pop("genres_modified")
                last_modified_time_persons = item.pop("persons_modified")

                for candidate_time in itertools.chain(
                    last_modified_time_genres,
                    last_modified_time_persons,
                ):
                    if isinstance(candidate_time, str):
                        candidate_time = datetime.strptime(
                            candidate_time,
                            "%m-%d-%Y %H:%M:%S",
                        )
                    if candidate_time:
                        if candidate_time > last_modified_time:
                            last_modified_time = candidate_time
        if last_modified_time_data > last_modified_time:
            last_modified_time = last_modified_time_data
        current_modified_time = self.local_storage.retrieve_state()
        if not current_modified_time or (
            last_modified_time > current_modified_time
        ):
            self.save_actual_state(last_modified_time)

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Generator, NoReturn
from uuid import UUID

import psycopg
from psycopg import ClientCursor
from psycopg.rows import dict_row


@dataclass
class MoviesData:
    id: str
    title: str
    description: str
    imdb_rating: float
    modified: datetime
    genres_modified: list
    persons_modified: list
    persons: list
    genres: list

    def __post_init__(self) -> NoReturn:
        if isinstance(self.id, UUID):
            self.id = str(self.id)


@dataclass
class GenresData:
    id: str
    name: str
    description: str
    modified: datetime

    def __post_init__(self) -> NoReturn:
        if isinstance(self.id, UUID):
            self.id = str(self.id)


@dataclass
class PersonsData:
    id: str
    name: str
    modified: datetime

    def __post_init__(self) -> NoReturn:
        if isinstance(self.id, UUID):
            self.id = str(self.id)


class PostgresExtractor:
    def __init__(
        self,
        dsl: Dict[str, Any],
        config: Dict[str, Any],
        modified_time: str,
    ) -> NoReturn:
        self._database_connection = None
        self.dsl = dsl
        self.config = config
        self.modified_time = modified_time

    def connect(self) -> psycopg.Connection:
        if not self._database_connection:
            try:
                self._database_connection = psycopg.connect(
                    **self.dsl,
                    row_factory=dict_row,
                    cursor_factory=ClientCursor,
                )
                return self._database_connection
            except psycopg.OperationalError:
                pass
            except BaseException:
                raise

    def movies_query(self):
        modified = self.modified_time.strftime("%m-%d-%Y %H:%M:%S")
        query = f"""\
            SELECT
            fw.id,
            fw.title,
            fw.description,
            fw.rating as imdb_rating,
            fw.modified,
            COALESCE (
                json_agg(
                    DISTINCT jsonb_build_object(
                        'person_role', pfw.role,
                        'person_id', p.id,
                        'person_name', p.full_name
                    )
                ) FILTER (WHERE p.id is not null),
                '[]'
            ) as persons,
            COALESCE (
                json_agg(
                    DISTINCT jsonb_build_object(
                        'id', g.id,
                        'name', g.name
                    )
                ) FILTER (WHERE g.id is not null),
                '[]'
            ) as genres,
            array_agg(DISTINCT g.modified) persons_modified,
            array_agg(DISTINCT p.modified) genres_modified
            FROM content.film_work fw
            LEFT JOIN content.person_film_work pfw
                        ON pfw.film_work_id = fw.id
            LEFT JOIN content.person p ON p.id = pfw.person_id
            LEFT JOIN content.genre_film_work gfw
                        ON gfw.film_work_id = fw.id
            LEFT JOIN content.genre g ON g.id = gfw.genre_id
            WHERE '{modified}' < any(array[
                DATE_TRUNC('second', fw.modified::timestamp),
                DATE_TRUNC('second', g.modified::timestamp),
                DATE_TRUNC('second', p.modified::timestamp)
            ])
            GROUP BY fw.id
            ORDER BY fw.modified
            """
        return query

    def genres_query(self):
        modified = self.modified_time.strftime("%m-%d-%Y %H:%M:%S")
        query = f"""\
            SELECT
            id,
            name,
            description,
            modified
            FROM content.genre
            WHERE '{modified}' < modified
            """
        return query

    def persons_query(self):
        modified = self.modified_time.strftime("%m-%d-%Y %H:%M:%S")
        query = f"""\
            SELECT
            id,
            full_name as name,
            modified
            FROM content.person
            WHERE '{modified}' < modified
            """
        return query

    def extract_data(
        self,
        cursor: psycopg.Cursor,
        raw_query: str,
    ) -> Generator:
        with closing(cursor) as pg_cur:
            try:
                pg_cur.execute(raw_query)
                while results := pg_cur.fetchmany(self.config["BATCH_SIZE"]):
                    yield results
            except BaseException:
                raise

    def transform_data(
        self,
        cursor: psycopg.Cursor,
        raw_query: str,
        source: str,
    ) -> Generator:
        for batch in self.extract_data(cursor, raw_query):
            match source:
                case "movies":
                    yield [MoviesData(**dict(item)) for item in batch]
                case "genres":
                    yield [GenresData(**dict(item)) for item in batch]
                case "persons":
                    yield [PersonsData(**dict(item)) for item in batch]

    def retrieve_data(self, raw_query: str, source: str) -> Generator:
        with closing(
            self._database_connection.cursor(row_factory=dict_row),
        ) as psql_cursor:
            for batch in self.transform_data(psql_cursor, raw_query, source):
                batch_as_tuples = [asdict(item) for item in batch]
                yield batch_as_tuples

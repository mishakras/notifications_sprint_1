from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    pg_dsn: str | None = os.getenv("PG_DSN")

    db_host: str = os.getenv("DB_HOST", "theatre-db")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("POSTGRES_DB", "theatre")
    db_user: str = os.getenv("POSTGRES_USER", "postgres")
    db_pass: str = os.getenv("POSTGRES_PASSWORD", "secret")

    es_host: str = os.getenv("ES_HOST") or os.getenv(
        "ELASTIC_HOST",
        "http://elastic:9200",
    )
    es_index: str = os.getenv("ES_INDEX", "movies")

    director_weight: int = int(os.getenv("DIRECTOR_WEIGHT", "2"))
    concurrent_queries: int = int(os.getenv("CONCURRENT_QUERIES", "4"))

    def effective_pg_dsn(self) -> str:
        if self.pg_dsn:
            return self.pg_dsn
        return (
            "postgresql://"
            f"{self.db_user}: {self.db_pass}"
            f"@{self.db_host}: {self.db_port}/{self.db_name}"
        )


SETTINGS = Settings()

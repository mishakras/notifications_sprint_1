from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOP = "develop"
    STAGING = "staging"
    PRODUCTION = "production"


class AppSettings(BaseModel):
    title: str = "Movies"
    description: str = "Сервис пользовательских оценок"
    version: str = "0.0.1"
    docs_url: str = "/api/openapi"
    openapi_url: str = "/api/openapi.json"
    redoc_url: str = "/api/redoc"
    debug: bool = False
    cache_ttl: int = 60 * 60 * 1  # 1 час
    request_limit_per_minute: int = Field(
        20,
        validation_alias=AliasChoices(
            "REQUEST_LIMIT_PER_MINUTE",
            "APP__REQUEST_LIMIT_PER_MINUTE",
        ),
    )
    environment: Environment = Field(
        default=Environment.DEVELOP,
        validation_alias=AliasChoices("ENVIRONMENT", "APP__ENVIRONMENT"),
    )
    zero_request_id: UUID = UUID("00000000-0000-0000-0000-000000000000")


class LocalSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class LogstashSettings(BaseModel):
    host: str = Field(
        "logstash",
        validation_alias=AliasChoices("LOGSTASH_HOST", "LOGSTASH__HOST"),
    )
    port: int = Field(
        5044,
        validation_alias=AliasChoices("LOGSTASH_PORT", "LOGSTASH__PORT"),
    )
    tag: str = Field(
        "notification",
        validation_alias=AliasChoices("LOGSTASH_TAG", "LOGSTASH__TAG"),
    )


class PostgresSettings(BaseModel):
    user: str = Field(
        "postgres",
        validation_alias=AliasChoices(
            "POSTGRES_USER",
            "POSTGRES__USER",
        ),
    )
    password: str = Field(
        "secret",
        validation_alias=AliasChoices(
            "POSTGRES_PASSWORD",
            "POSTGRES__PASSWORD",
        ),
    )
    host: str = Field(
        "theatre-db",
        validation_alias=AliasChoices(
            "DB_HOST",
            "DB__HOST",
            "POSTGRES_HOST",
            "POSTGRES__HOST",
        ),
    )
    dbname: str = Field(
        "theatre",
        validation_alias=AliasChoices(
            "POSTGRES_DB",
            "POSTGRES__DB",
            "DB_NAME",
            "DB__NAME",
        ),
    )


class KafkaSettings(BaseModel):
    host: str = Field(
        "kafka",
        validation_alias=AliasChoices(
            "KAFKA_HOST",
            "KAFKA__HOST",
        ),
    )
    port: int = Field(
        9092,
        validation_alias=AliasChoices(
            "KAFKA_PORT",
            "KAFKA__PORT",
        ),
    )
    topic: str = Field(
        "notifications",
        validation_alias=AliasChoices(
            "KAFKA_TOPIC",
            "KAFKA__TOPIC",
        ),
    )

    @computed_field
    @property
    def server(self) -> str:
        return f"{self.host}:{self.port}"


# В проде читаем только из env; локально — можно положить .env рядом с репо
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            None
            if os.getenv("DOCKER")
            else str(Path(__file__).parent.parent.parent / ".env")
        ),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app: AppSettings = AppSettings()
    local: LocalSettings = LocalSettings()
    kafka: KafkaSettings = KafkaSettings()
    logstash: LogstashSettings = LogstashSettings()
    postgres: PostgresSettings = PostgresSettings()


settings = Settings()

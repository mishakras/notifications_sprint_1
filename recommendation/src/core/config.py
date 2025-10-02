import os
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOP = "develop"
    STAGING = "staging"
    PRODUCTION = "production"


class AppSettings(BaseModel):
    title: str = "Recommendations"
    description: str = "Сервис пользовательских рекомендаций"
    version: str = "0.0.1"
    docs_url: str = "/api/openapi"
    openapi_url: str = "/api/openapi.json"
    redoc_url: str = "/api/redoc"
    debug: bool = False
    cache_ttl: int = 60 * 60 * 1
    request_limit_per_minute: int = 20
    environment: Environment = Environment.DEVELOP
    zero_request_id: UUID = UUID("00000000-0000-0000-0000-000000000000")


class LocalSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class LogstashSettings(BaseModel):
    host: str = ""
    port: int = 0
    tag: str = "recommendations"


class MongoDBConfig(BaseModel):
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    name: str = "user_likes"

    @computed_field
    @property
    def database_url(self) -> str:
        """URL для подключения к MongoDB"""

        return (
            f"mongodb://{self.username}:{self.password}"
            f"@{self.host}:{self.port}"
        )


class ElasticSettings(BaseModel):
    host: str = ""
    port: str = ""

    @computed_field
    @property
    def elastic_url(self) -> str:
        """URL для подключения к Elasticsearch"""

        return f"http://{self.host}:{self.port}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            [
                str(Path(__file__).parents[3] / "common/.env"),
                str(Path(__file__).parents[2] / ".env"),
            ]
            if not os.getenv("DOCKER")
            else None
        ),
        env_nested_delimiter="_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    app: AppSettings = AppSettings()
    local: LocalSettings = LocalSettings()
    logstash: LogstashSettings = LogstashSettings()
    mongo: MongoDBConfig = MongoDBConfig()
    elastic: ElasticSettings = ElasticSettings()
    dev: Environment = Environment.DEVELOP


settings = Settings()

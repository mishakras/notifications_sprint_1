import os
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from dotenv import dotenv_values
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

config = {
    **dotenv_values("/opt/common/.env"),
}


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class AppSettings(BaseModel):
    title: str = "Movies"
    description: str = "Сервис пользовательского оценок"
    version: str = "0.0.1"
    docs_url: str = "/api/openapi"
    openapi_url: str = "/api/openapi.json"
    redoc_url: str = "/api/redoc"
    debug: bool = False
    cache_ttl: int = 60 * 60 * 1  # 1 час
    request_limit_per_minute: int = int(
        config.get("REQUEST_LIMIT_PER_MINUTE", 20),
    )
    environment: str = config.get("ENVIRONMENT", Environment.DEVELOPMENT)
    zero_request_id: UUID = UUID("00000000-0000-0000-0000-000000000000")


class LocalSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class LogstashSettings(BaseModel):
    host: str = config["LOGSTASH_HOST"]
    port: int = int(config["LOGSTASH_PORT"])
    tag: str = "content_service"


class RedisSettings(BaseModel):
    redis_host: str = config["REDIS_HOST"]
    redis_port: str = config["REDIS_PORT"]


class ElasticSettings(BaseModel):
    elastic_host: str = config["ELASTIC_HOST"]
    elastic_port: str = config["ELASTIC_PORT"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            None
            if os.getenv("DOCKER")
            else str(Path(__file__).parent.parent.parent / ".env")
        ),
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    app: AppSettings = AppSettings()
    local: LocalSettings = LocalSettings()
    redis: RedisSettings = RedisSettings()
    logstash: LogstashSettings = LogstashSettings()
    elastic: ElasticSettings = ElasticSettings()
    envEnum: Environment = Environment


settings = Settings()

import logging
import os
from logging import config as logging_config
from pathlib import Path

from app.common.kafka_etl_configs import TopicSettings
from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import LOGGING

logging_config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    title: str = "UGC Service"
    description: str = "Сервис пользовательского контента"
    version: str = "0.0.1"
    docs_url: str = "/api/v1/ugc/openapi"
    openapi_url: str = "/api/v1/ugc/openapi.json"
    redoc_url: str = "/api/v1/ugc/redoc"
    debug: bool = False


class LocalSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class MongoDBConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 27017121
    username: str = "mongodb"
    password: str = "mongodb"
    name: str = "ugc"

    @computed_field
    @property
    def database_url(self) -> str:
        """URL для подключения к MongoDB"""
        return (
            f"mongodb://{self.username}:{self.password}"
            f"@{self.host}:{self.port}"
        )


class KafkaSettings(BaseModel):
    host: str = "172.28.0.90"
    port: int = 9094

    @computed_field
    @property
    def server(self) -> str:
        return f"{self.host}:{self.port}"


class SentrySettings(BaseModel):
    dsn: str = "link"
    able: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).parent.parent.parent.parent / "common/.env")
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
    mongo: MongoDBConfig = MongoDBConfig()
    topic: TopicSettings = TopicSettings()
    kafka: KafkaSettings = KafkaSettings()
    sentry: SentrySettings = SentrySettings()


settings = Settings()

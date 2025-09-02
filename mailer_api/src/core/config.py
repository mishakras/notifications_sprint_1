import os
from pathlib import Path
from uuid import UUID

from dotenv import dotenv_values
from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

config = {
    **dotenv_values("/opt/common/.env"),
}


class AppSettings(BaseModel):
    title: str = "User actions"
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
    environment: str = config.get("ENVIRONMENT", "develop")
    zero_request_id: UUID = UUID("00000000-0000-0000-0000-000000000000")


class LocalSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class URLSettings(BaseModel):
    films_url: str = config["FILMS_URL"]


class LogstashSettings(BaseModel):
    host: str = config["LOGSTASH_HOST"]
    port: int = int(config["LOGSTASH_PORT"])


class YandexSettings(BaseModel):
    yandex_host: str = config["YANDEX_HOST"]
    yandex_port: int = int(config["YANDEX_PORT"])
    yandex_login: str = config["YANDEX_LOGIN"]
    yandex_password: str = config["YANDEX_PASSWORD"]


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
    yandex: YandexSettings = YandexSettings()
    logstash: LogstashSettings = LogstashSettings()
    urls: URLSettings = URLSettings()


settings = Settings()

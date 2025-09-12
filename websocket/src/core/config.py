import os
from pathlib import Path
from uuid import UUID

from dotenv import dotenv_values
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

config = {
    **dotenv_values("/opt/common/.env"),
}


class AppSettings(BaseModel):
    title: str = "Web sokets"
    description: str = "Сервис вебсокетов"
    version: str = "0.0.1"
    debug: bool = False
    environment: str = config.get("ENVIRONMENT", "develop")
    zero_request_id: UUID = UUID("00000000-0000-0000-0000-000000000000")


class LocalSettings(BaseModel):
    host: str = "localhost"
    port: int = "8080"


class LogstashSettings(BaseModel):
    host: str = config["LOGSTASH_HOST"]
    port: int = int(config["LOGSTASH_PORT"])
    tag: str = "websocket_api"


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
    logstash: LogstashSettings = LogstashSettings()


settings = Settings()

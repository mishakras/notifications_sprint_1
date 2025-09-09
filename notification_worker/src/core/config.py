import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

config = {
    **dotenv_values("/opt/common/.env"),
}


class LogstashSettings(BaseModel):
    host: str = config.get("LOGSTASH_HOST", "logstash")
    port: int = int(config.get("LOGSTASH_PORT", 5000))
    tag: str = "notification_worker"


class AuthServiceSettings(BaseModel):
    url: str = config.get("AUTH_SERVICE_URL", "http://auth_service:8000")
    timeout: int = 30


class KafkaSettings(BaseModel):
    host: str = config["KAFKA_HOST"]
    port: str = config["KAFKA_PORT"]
    topic: str = "notifications"
    group_id: str = "notification_workers"

    @computed_field
    @property
    def server(self) -> str:
        return f"{self.host}:{self.port}"


class PostgresSettings(BaseModel):
    user: str = config["POSTGRES_USER"]
    password: int = config["POSTGRES_PASSWORD"]
    host: str = config["DB_HOST"]
    database: str = config["POSTGRES_DB"]


class RedisSettings(BaseModel):
    host: str = config.get("REDIS_HOST", "redis")
    port: int = int(config.get("REDIS_PORT", 6379))
    db: int = 0


class EmailSettings(BaseModel):
    host: str = config.get("EMAIL_HOST", "smtp.gmail.com")
    port: int = int(config.get("EMAIL_PORT", 587))
    username: str = config.get("EMAIL_USERNAME", "")
    password: str = config.get("EMAIL_PASSWORD", "")
    use_tls: bool = True


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

    kafka: KafkaSettings = KafkaSettings()
    auth: AuthServiceSettings = AuthServiceSettings()
    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    email: EmailSettings = EmailSettings()
    logstash: LogstashSettings = LogstashSettings()
    shortener_url: str = config.get("SHORTENER_URL", "http://shortener:8888")
    max_retries: int = 3
    retry_delay: int = 5
    processing_timeout: int = 30


settings = Settings()

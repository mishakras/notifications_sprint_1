import os
from pathlib import Path

from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import Environment


class LogstashSettings(BaseModel):
    host: str = "logstash"
    port: int = 5000
    tag: str = "notification_worker"


class AuthServiceSettings(BaseModel):
    url: str = "http://auth_service:8000"
    timeout: int = 30


class KafkaSettings(BaseModel):
    host: str = "kafka"
    port: str = "9092"
    topic: str = "notifications"
    group_id: str = "notification_workers"
    dlq_topic: str = "notifications_dlq"

    @computed_field
    @property
    def server(self) -> str:
        return f"{self.host}:{self.port}"


class PostgresSettings(BaseModel):
    user: str = "postgres"
    password: str = "postgres"
    host: str = "postgres"
    database: str = "notifications"


class RedisSettings(BaseModel):
    host: str = "redis"
    port: int = 6379
    db: int = 0


class EmailSettings(BaseModel):
    host: str = "mailpit"
    port: int = 1025
    username: str = ""
    password: str = ""
    use_tls: bool = False
    from_email: str = "noreply@cinema.com"
    from_name: str = "Cinema Notifications"


class SMSSettings(BaseModel):
    enabled: bool = False
    provider: str = "mock"
    api_key: str = ""
    api_url: str = ""


class PushSettings(BaseModel):
    enabled: bool = False
    provider: str = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            None
            if os.getenv("DOCKER")
            else str(Path(__file__).parents[4] / "common/.env")
        ),
        env_nested_delimiter="__",
        env_prefix="NOTIFICATION_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = Environment.DEVELOPMENT
    kafka: KafkaSettings = KafkaSettings()
    auth: AuthServiceSettings = AuthServiceSettings()
    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    email: EmailSettings = EmailSettings()
    sms: SMSSettings = SMSSettings()
    push: PushSettings = PushSettings()
    logstash: LogstashSettings = LogstashSettings()
    shortener_url: str = "http://shortener:8888"
    max_retries: int = 3
    retry_delay: int = 5
    processing_timeout: int = 30


settings = Settings()

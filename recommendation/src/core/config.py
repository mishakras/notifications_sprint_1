from enum import StrEnum
from uuid import UUID

from dotenv import dotenv_values
from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings

config = {
    **dotenv_values("/app/common/.env"),
}


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
    request_limit_per_minute: int = int(
        config.get("REQUEST_LIMIT_PER_MINUTE", 20),
    )
    environment: str = config.get("ENVIRONMENT", Environment.DEVELOP)
    zero_request_id: UUID = UUID("00000000-0000-0000-0000-000000000000")


class LogstashSettings(BaseModel):
    host: str = config.get("LOGSTASH_HOST", Environment.DEVELOP)
    port: int = config.get("LOGSTASH_PORT", Environment.DEVELOP)
    tag: str = "recommendations"


class LocalSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1


class MongoDBConfig(BaseModel):
    host: str = config["MONGO_HOST"]
    port: int = config["MONGO_PORT"]
    username: str = config["MONGO_USERNAME"]
    password: str = config["MONGO_PASSWORD"]
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
    host: str = config["ELASTIC_HOST"]
    port: str = config["ELASTIC_PORT"]

    @computed_field
    @property
    def elastic_url(self) -> str:
        """URL для подключения к Elasticsearch"""

        return f"http://{self.host}:{self.port}"


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    local: LocalSettings = LocalSettings()
    mongo: MongoDBConfig = MongoDBConfig()
    logstash: LogstashSettings = LogstashSettings()
    elastic: ElasticSettings = ElasticSettings()
    dev: Environment = Environment.DEVELOP


settings = Settings()

from dotenv import dotenv_values
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from common.kafka_etl_configs import TopicSettings

config = {
    **dotenv_values("/opt/common/.env"),
}


class ClickHouseSettings(BaseModel):
    host: str = config["CLICKHOUSE_HOST"]


class KafkaSettings(BaseModel):
    host: str = config["KAFKA_HOST"]
    port: str = config["KAFKA_PORT"]


class Settings(BaseSettings):
    kafka: KafkaSettings = KafkaSettings()
    clickhouse: ClickHouseSettings = ClickHouseSettings()
    topics: TopicSettings = TopicSettings()


settings = Settings()

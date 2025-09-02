import os
from pathlib import Path

from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MainConfig(BaseModel):
    data_volume: int = Field(
        default=10_000_000,
        description="Количество записей для тестирования",
    )
    batch_sizes: list[int] = Field(
        default=[1000, 5000, 10000, 25000, 50000, 100000],
    )
    num_processes: int = Field(default=6)
    test_iterations: int = Field(default=3)
    target_response_time: float = Field(
        default=0.2,
        description="Целевое время отклика в секундах (200 мс)",
    )


class MongoConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=27017)
    username: str = Field(default="mongo")
    password: str = Field(default="mongo")
    database: str = Field(default="user_behavior")
    connection_string: str = ""

    @computed_field
    def get_connection_string(self) -> str:
        if self.username and self.password:
            return (
                f"mongodb://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?authSource=admin"
            )
        else:
            return f"mongodb://{self.host}:{self.port}/{self.database}"


class PostgresConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    username: str = Field(default="postgres")
    password: str = Field(default="postgres")
    database: str = Field(default="user_behavior")
    connection_string: str = ""

    @computed_field
    def get_connection_string(self) -> str:
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_nested_delimiter="_",
        env_file=(
            None
            if os.getenv("DOCKER")
            else str(Path(__file__).parent / ".env")
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    proj: MainConfig = MainConfig()
    mongo_db: MongoConfig = MongoConfig()
    pg_db: PostgresConfig = PostgresConfig()


settings = Settings()

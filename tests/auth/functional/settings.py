from pydantic import Field
from pydantic_settings import BaseSettings
from yarl import URL

from tests.auth.functional.utils.config import config


class TestSettings(BaseSettings):
    service_url: str = "http://nginx/api/v1/"
    database_user: str = Field(config["POSTGRES_USER"], alias="POSTGRES_USER")
    database_password: str = Field(
        config["POSTGRES_PASSWORD"],
        alias="POSTGRES_PASSWORD",
    )
    database_host: str = Field(config["DB_HOST"], alias="DB_HOST")
    database_name: str = Field(config["AUTH_DB"], alias="AUTH_DB")
    database_port: int = 5432

    def get_connection_string(self):
        return str(
            URL.build(
                scheme="postgresql+asyncpg",
                user=self.database_user,
                password=self.database_password,
                host=self.database_host,
                path=f"/{self.database_name}",
            ),
        )


test_settings = TestSettings()

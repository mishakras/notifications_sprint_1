from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    review_api_url: str = Field("http://172.28.0.130:8000")


test_settings = TestSettings()

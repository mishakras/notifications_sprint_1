from pydantic import Field
from pydantic_settings import BaseSettings

from auth_service.src.utils.config import config


class OAuthGoogleSettings(BaseSettings):
    client_id: str = Field(
        config["GOOGLE_CLIENT_ID"],
        alias="GOOGLE_CLIENT_ID",
    )
    client_secret: str = Field(
        config["GOOGLE_CLIENT_SECRET"],
        alias="GOOGLE_CLIENT_SECRET",
    )
    scope: str = "openid email profile"
    server_metadata_url: str = Field(
        config["GOOGLE_METADATA_URL"],
        alias="GOOGLE_METADATA_URL",
    )


class OAuthYandexSettings(BaseSettings):
    client_id: str = Field(
        config["YANDEX_CLIENT_ID"],
        alias="YANDEX_CLIENT_ID",
    )
    client_secret: str = Field(
        config["YANDEX_CLIENT_SECRET"],
        alias="YANDEX_CLIENT_SECRET",
    )
    scope: str = "login:email"
    api_base_url: str = "https://login.yandex.ru/"
    authorize_url: str = "https://oauth.yandex.ru/authorize"
    access_token_url: str = "https://oauth.yandex.ru/token"
    redirect_uri: str = Field(
        config["YANDEX_REDIRECT_URI"],
        alias="YANDEX_REDIRECT_URI",
    )

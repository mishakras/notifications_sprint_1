import uuid
from abc import ABC, abstractmethod

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from auth_lib.utils import generate_random_string
from auth_service.src.auth.auth import hash_password
from auth_service.src.auth.oauth_settings import (
    OAuthGoogleSettings,
    OAuthYandexSettings,
)
from auth_service.src.repositories.auth.social_account import (
    SocialAccountRepository,
    social_account_repository,
)
from auth_service.src.repositories.auth.users import (
    UserRepository,
    user_repository,
)
from auth_service.src.schemas.auth.social_account import SocialAccountCreate
from auth_service.src.schemas.auth.users import OAuthUserData, UserCreate
from auth_service.src.services.auth.auth import AuthService, auth_service


class BaseProvider(ABC):
    def __init__(self, client, provider_name):
        self.client = client
        self.provider_name = provider_name

    @abstractmethod
    async def parse_token(self, token) -> OAuthUserData:
        raise NotImplementedError

    async def redirect(self, request, endpoint) -> RedirectResponse:
        redirect_uri = request.url_for(endpoint, name=self.provider_name)
        return await self.client.authorize_redirect(request, redirect_uri)

    async def authorize_access_token(self, request):
        return await self.client.authorize_access_token(request)


class GoogleProvider(BaseProvider):
    async def parse_token(self, token) -> OAuthUserData | None:
        user_data = token.get("userinfo")
        user_id = user_data["sub"]
        user_email = user_data["email"]
        return OAuthUserData(user_id=user_id, email=user_email)


class YandexProvider(BaseProvider):
    async def parse_token(self, token) -> OAuthUserData | None:
        response = (await self.client.get("info", token=token)).json()
        user_id = response["id"]
        user_email = response["default_email"]
        return OAuthUserData(user_id=user_id, email=user_email)


def get_provider(client, provider):
    factory_dict = {
        "google": GoogleProvider,
        "yandex": YandexProvider,
    }

    return factory_dict[provider](client, provider)


class OAuthService:
    def __init__(
        self,
        account_repository: SocialAccountRepository,
        user_repository: UserRepository,
        auth_service: AuthService,
    ):
        self.account_repository = account_repository
        self.user_repository = user_repository
        self.auth_service = auth_service

        self.oauth = OAuth()
        self._register_providers()

    async def redirect(self, request, name, endpoint: str):
        client = await self._get_client(name)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client '{name}' not found",
            )

        return await client.redirect(request, endpoint)

    async def auth(self, request, name):
        client = await self._get_client(name)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Client '{name}' not found",
            )

        token = await client.authorize_access_token(request)
        user_data = await client.parse_token(token)

        current_account = await self.account_repository.read(
            social_id=user_data.user_id,
            social_name=user_data.email,
        )

        if current_account:
            current_user = await self.user_repository.read(
                id=current_account.user_id,
            )
        else:
            new_user = UserCreate(
                email=str(user_data.email),
                hashed_password=hash_password(
                    generate_random_string(),
                ),
                is_superuser=False,
            )

            current_user = await self.user_repository.create(
                data=new_user.model_dump(),
            )

            await self.account_repository.create(
                data=SocialAccountCreate(
                    id=uuid.uuid4(),
                    social_id=user_data.user_id,
                    social_name=user_data.email,
                    user_id=current_user.id,
                ).model_dump(),
            )

        return await self.auth_service.social_authentication(current_user)

    def _register_providers(self):
        google_settings = OAuthGoogleSettings()
        self.oauth.register(
            name="google",
            client_id=google_settings.client_id,
            client_secret=google_settings.client_secret,
            server_metadata_url=google_settings.server_metadata_url,
            client_kwargs={"scope": google_settings.scope},
        )

        yandex_settings = OAuthYandexSettings()
        self.oauth.register(
            name="yandex",
            client_id=yandex_settings.client_id,
            client_secret=yandex_settings.client_secret,
            authorize_url=yandex_settings.authorize_url,
            access_token_url=yandex_settings.access_token_url,
            redirect_uri=yandex_settings.redirect_uri,
            api_base_url=yandex_settings.api_base_url,
            client_kwargs={"scope": yandex_settings.scope},
        )

    async def _get_client(self, name) -> BaseProvider:
        client = self.oauth.create_client(name)
        return get_provider(client, name)


def get_oauth_service() -> OAuthService:
    return OAuthService(
        social_account_repository,
        user_repository,
        auth_service,
    )

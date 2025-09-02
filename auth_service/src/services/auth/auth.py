from datetime import datetime, timedelta

from fastapi import Request

from auth_service.src.auth.auth import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
    verify_token,
)
from auth_service.src.auth.exceptions import (
    AlreadyRegisteredUserException,
    InvalidCredentialsException,
    InvalidTokenSignatureException,
    NoLoginHistoryFoundException,
    OldPasswordIsIncorrectException,
    UserNotFoundException,
)
from auth_service.src.models.auth.db_models import User
from auth_service.src.schemas.auth.users import (
    UserCreate,
    UserCredentialsRequest,
    UserUpdate,
    UserUpdateCredentials,
)
from auth_service.src.services.auth.history import (
    HistoryService,
    history_service,
)
from auth_service.src.services.auth.tokens import TokenService, token_service
from auth_service.src.services.auth.users import UserService, user_service


class AuthService:
    def __init__(
        self,
        user_serv: UserService,
        token_serv: TokenService,
        history_serv: HistoryService,
    ):
        self._user_service = user_serv
        self._token_service = token_serv
        self._history_service = history_serv

    async def register(
        self,
        new_user: UserCredentialsRequest,
    ):
        user = await self._user_service.get_by_email(str(new_user.email))
        if user:
            raise AlreadyRegisteredUserException(new_user.email)

        new_user = UserCreate(
            email=str(new_user.email),
            hashed_password=hash_password(
                new_user.password.get_secret_value(),
            ),
            is_superuser=False,
        )

        await self._user_service.create(new_user)

        return new_user

    async def login(
        self,
        login_data: UserCredentialsRequest,
        request: Request,
    ):
        user = await self._user_service.get_by_email(login_data.email)
        if not user or not verify_password(
            login_data.password.get_secret_value(),
            user.hashed_password,
        ):
            if user:
                await self._history_service.create(
                    user_id=user.id,
                    login_time=datetime.utcnow(),
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                    action="failure login",
                )
            raise InvalidCredentialsException

        refresh_token = create_token({"sub": user.email}, timedelta(hours=24))

        await self._token_service.create(
            user_id=user.id,
            refresh_token=refresh_token,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=3),
            revoked=False,
        )

        await self._history_service.create(
            user_id=user.id,
            login_time=datetime.utcnow(),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            action="successfully login",
        )

        user.last_login_at = datetime.utcnow()
        await self._user_service.update(
            user.id,
            UserUpdate.model_validate(user),
        )

        access_token = create_token({"sub": user.email}, timedelta(days=3))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(
        self,
        refresh_token: str,
    ):
        token_entry = await self._token_service.read(
            refresh_token=refresh_token,
        )
        if not token_entry:
            raise InvalidTokenSignatureException

        try:
            user_email = self._token_service.validate_token(token_entry)
        except Exception:
            raise InvalidTokenSignatureException

        new_refresh_token = create_token(
            {"sub": user_email},
            timedelta(hours=24),
        )

        await self._token_service.create(
            user_id=token_entry.user_id,
            refresh_token=new_refresh_token,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=3),
            revoked=False,
        )

        await self._history_service.create(
            user_id=token_entry.user_id,
            login_time=datetime.utcnow(),
            ip_address=None,
            user_agent=None,
            action="refresh tokens",
        )

        new_access_token = create_token(
            {"sub": user_email},
            timedelta(hours=3),
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(
        self,
        access_token: str,
        request: Request,
    ):
        payload = decode_token(access_token)
        if not payload:
            raise InvalidTokenSignatureException

        user_email = payload.get("sub")

        user = await self._user_service.get_by_email(user_email)
        if not user:
            raise UserNotFoundException

        await self._token_service.clear_token_by_user_id(user.id)

        await self._history_service.create(
            user_id=user.id,
            login_time=datetime.utcnow(),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            action="successfully logout",
        )

    async def change_credentials(
        self,
        access_token: str,
        user_credentials: UserUpdateCredentials,
    ):
        email = await verify_token(access_token)

        user = await self._user_service.get_by_email(email)
        if not user:
            raise InvalidTokenSignatureException

        if not verify_password(
            user_credentials.old_password.get_secret_value(),
            user.hashed_password,
        ):
            raise OldPasswordIsIncorrectException

        if user_credentials.email != user.email:
            user_check = await self._user_service.get_by_email(
                user_credentials.email,
            )
            if user_check:
                raise AlreadyRegisteredUserException

        user_update = UserUpdate(
            email=str(user_credentials.email),
            hashed_password=hash_password(
                user_credentials.password.get_secret_value(),
            ),
            is_superuser=False,
        )
        await self._user_service.update(user.id, user_update)

        await self._history_service.create(
            user_id=user.id,
            login_time=datetime.utcnow(),
            ip_address="not available",
            user_agent="not available",
            action="credentials changed",
        )

        access_token = create_token({"sub": user.email}, timedelta(hours=3))

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    async def get_login_history(
        self,
        token: str,
    ):
        email = await verify_token(token)

        user = await self._user_service.get_by_email(email)
        if not user:
            raise InvalidTokenSignatureException

        history = await self._history_service.get_list_by_user_id(user.id)
        history.sort(key=lambda x: x.login_time, reverse=True)

        if not history:
            raise NoLoginHistoryFoundException

        return history

    async def social_authentication(
        self,
        user_data: User,
    ):
        new_refresh_token = create_token(
            {"sub": user_data.email},
            timedelta(hours=24),
        )

        await self._token_service.create(
            user_id=user_data.id,
            refresh_token=new_refresh_token,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=3),
            revoked=False,
        )

        await self._history_service.create(
            user_id=user_data.id,
            login_time=datetime.utcnow(),
            ip_address=None,
            user_agent=None,
            action="successfully login",
        )

        new_access_token = create_token(
            {"sub": user_data.email},
            timedelta(hours=3),
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }


auth_service = AuthService(user_service, token_service, history_service)


async def get_auth_service():
    yield auth_service

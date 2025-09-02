from datetime import datetime

import sqlalchemy

from auth_service.src.auth.auth import decode_token
from auth_service.src.repositories.auth.refresh_token import (
    refresh_token_repository,
)
from auth_service.src.repositories.base_repository import AbstractRepository
from auth_service.src.schemas.auth.refresh_token import (
    RefreshTokenCreate,
    RefreshTokenUpdate,
)


class TokenService:
    def __init__(self, repository: AbstractRepository):
        self.repository = repository

    async def create(self, **kwargs):
        user_id = kwargs.get("user_id")

        await self.clear_token_by_user_id(user_id)

        refresh_token = RefreshTokenCreate(**kwargs)

        await self.repository.create(data=refresh_token.model_dump())

    async def read(self, refresh_token):
        return await self.repository.read(refresh_token=refresh_token)

    async def clear_token_by_user_id(self, user_id):
        try:
            current_token = await refresh_token_repository.read(
                user_id=user_id,
            )
        except sqlalchemy.exc.NoResultFound:
            return

        if current_token:
            current_token.revoked = True
            await self.repository.update(
                data=RefreshTokenUpdate.model_validate(
                    current_token,
                ).model_dump(),
                user_id=user_id,
                issued_at=current_token.issued_at,
            )

    @staticmethod
    def validate_token(token_entry):
        if token_entry.expires_at < datetime.utcnow() or token_entry.revoked:
            raise Exception("Refresh token expired or revoked")

        payload = decode_token(token_entry.refresh_token)
        user_email = payload.get("sub")

        if not user_email:
            raise Exception("Invalid token")

        return user_email


token_service = TokenService(repository=refresh_token_repository)


async def get_token_service():
    yield token_service

from auth_service.src.auth.auth import decode_token
from auth_service.src.auth.exceptions import (
    InvalidTokenSignatureException,
    UserNotFoundException,
)
from auth_service.src.repositories.auth.users import user_repository
from auth_service.src.repositories.base_repository import AbstractRepository
from auth_service.src.schemas.auth.users import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: AbstractRepository):
        self.repository = repository

    async def get_by_email(self, user_email):
        user = await self.repository.read(email=user_email)
        return user

    async def create(self, user: UserCreate):
        await self.repository.create(data=user.model_dump())

    async def update(self, user_id: int, user: UserUpdate):
        await self.repository.update(data=user.model_dump(), id=user_id)

    async def get_user_data(
        self,
        access_token: str,
    ):
        user_email = get_user_email(access_token)

        user = await self.get_by_email(user_email)
        if not user:
            raise UserNotFoundException
        return user

    async def get_user_roles(
        self,
        access_token: str,
    ):
        return await self.repository.get_user_roles(
            email=get_user_email(access_token),
        )


user_service = UserService(repository=user_repository)


def get_user_email(access_token: str):
    payload = decode_token(access_token)
    if not payload:
        raise InvalidTokenSignatureException

    return payload.get("sub")


async def get_user_service():
    yield user_service

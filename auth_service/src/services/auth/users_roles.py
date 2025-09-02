from fastapi import status

from auth_service.src.auth.exceptions import (
    CustomHTTPException,
    RoleNotFoundException,
    UserNotFoundException,
)
from auth_service.src.repositories.auth.user_role import user_role_repository
from auth_service.src.repositories.base_repository import AbstractRepository
from auth_service.src.schemas.auth.roles import RoleResponseV1
from auth_service.src.schemas.auth.users import UserWithRoleResponseV1
from auth_service.src.schemas.auth.users_roles import UserRole
from auth_service.src.services.auth.roles import RoleService, role_service
from auth_service.src.services.auth.users import UserService, user_service


class UserRoleService:
    def __init__(
        self,
        user_service: UserService,
        role_service: RoleService,
        repository: AbstractRepository,
    ):
        self.repository = repository
        self._user_service = user_service
        self._role_service = role_service

    async def assign(
        self,
        user_email: str,
        role_name: str,
    ) -> UserWithRoleResponseV1:
        if not (user := await self._user_service.get_by_email(user_email)):
            raise UserNotFoundException(status.HTTP_404_NOT_FOUND)

        if not (role := await self._role_service.get_by_name(role_name)):
            raise RoleNotFoundException

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )

        await self.repository.create(data=user_role.model_dump())

        return UserWithRoleResponseV1(
            email=user.email,
            role=RoleResponseV1(
                id=role.id,
                name=role.name,
            ),
        )

    async def unassign(
        self,
        user_email: str,
        role_name: str,
    ) -> UserWithRoleResponseV1:
        if not (user := await self._user_service.get_by_email(user_email)):
            raise UserNotFoundException(status.HTTP_404_NOT_FOUND)

        if not (role := await self._role_service.get_by_name(role_name)):
            raise RoleNotFoundException

        if not (
            _ := await self.repository.read(user_id=user.id, role_id=role.id),
        ):
            raise CustomHTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have that role",
            )

        await self.repository.delete(user_id=user.id, role_id=role.id)

        return UserWithRoleResponseV1(
            email=user.email,
            role=RoleResponseV1(
                id=role.id,
                name=role.name,
            ),
        )


user_role_service = UserRoleService(
    repository=user_role_repository,
    user_service=user_service,
    role_service=role_service,
)


def get_user_role_service() -> UserRoleService:
    return user_role_service

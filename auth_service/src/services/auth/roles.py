from auth_service.src.auth.exceptions import (
    AlreadyRegisteredRoleException,
    RoleNotFoundException,
)
from auth_service.src.repositories.auth.roles import role_repository
from auth_service.src.repositories.base_repository import AbstractRepository
from auth_service.src.schemas.auth.roles import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, repository: AbstractRepository):
        self.repository = repository

    async def create(self, name) -> RoleCreate:
        if _ := await self.repository.read(name=name):
            raise AlreadyRegisteredRoleException

        new_role = await self.repository.create(
            data=RoleCreate(name=name).model_dump(),
        )

        return new_role

    async def update(self, role_id, new_name) -> RoleUpdate:
        if not (current_role := await self.repository.read(id=role_id)):
            raise RoleNotFoundException

        update_role = RoleUpdate(id=current_role.id, name=new_name)
        await self.repository.update(data=update_role.model_dump())

        return update_role

    async def delete(self, role_id) -> RoleCreate:
        if not (current_role := await self.repository.read(id=role_id)):
            raise RoleNotFoundException

        await self.repository.delete(id=role_id)

        return RoleCreate.model_validate(current_role)

    async def get_list(self, role_name: str):
        if not role_name:
            return await self.repository.read_list()
        else:
            return await self.repository.read_list_by_filter(name=role_name)

    async def get_list_by_ids(self, ids: list[int]):
        if not ids:
            return await self.repository.read_list()
        else:
            return await self.repository.read_list_by_filter(id=ids)

    async def get_by_name(self, role_name) -> RoleCreate:
        role = await self.repository.read(name=role_name)
        return RoleCreate.model_validate(role)


role_service = RoleService(repository=role_repository)


def get_role_service() -> RoleService:
    return role_service

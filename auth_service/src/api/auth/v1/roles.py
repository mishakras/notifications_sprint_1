import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2AuthorizationCodeBearer

from auth_lib.utils import get_token_from_request
from auth_service.src.api.swagger import (
    assign_role_schema,
    create_role_schema,
    delete_role_schema,
    roles_listing_schema,
    unassign_role_schema,
    update_role_schema,
)
from auth_service.src.auth.auth import verify_token  # noqa: I005
from auth_service.src.core import logger
from auth_service.src.schemas.auth.roles import RoleResponseV1
from auth_service.src.schemas.auth.users import UserWithRoleResponseV1
from auth_service.src.services.auth.roles import RoleService, get_role_service
from auth_service.src.services.auth.users import UserService, get_user_service
from auth_service.src.services.auth.users_roles import (
    UserRoleService,
    get_user_role_service,
)

router = APIRouter()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl="/login",
    authorizationUrl="/auth",
)


def is_superuser():
    async def super_user_checker(
        request: Request,
        user_service: UserService = Depends(get_user_service),
    ):
        x_token = get_token_from_request(request)

        email = await verify_token(x_token)

        user = await user_service.get_by_email(email)
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient rights",
            )

    return super_user_checker


@router.post(
    "/create",
    response_model=RoleResponseV1,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(is_superuser())],
    **create_role_schema,
)
@logger.info(os.path.basename(__file__))
async def create(
    name: str,
    role_service: RoleService = Depends(get_role_service),
):
    new_role = await role_service.create(name)
    return RoleResponseV1.model_validate(new_role, from_attributes=True)


@router.get(
    "/",
    response_model=list[RoleResponseV1],
    dependencies=[Depends(is_superuser())],
    **roles_listing_schema,
)
@logger.info(os.path.basename(__file__))
async def get_list(
    name: str = Query("", alias="role_name", description="Role name"),
    service: RoleService = Depends(get_role_service),
):
    results = await service.get_list(name)
    return [
        RoleResponseV1.model_validate(row, from_attributes=True)
        for row in results
    ]


@router.put(
    "/{role_id}",
    response_model=RoleResponseV1,
    dependencies=[Depends(is_superuser())],
    **update_role_schema,
)
@logger.info(os.path.basename(__file__))
async def update(
    role_id: int,
    name: str,
    role_service: RoleService = Depends(get_role_service),
):
    result = await role_service.update(role_id, name)
    return RoleResponseV1.model_validate(result, from_attributes=True)


@router.delete(
    "/{role_id}",
    response_model=RoleResponseV1,
    dependencies=[Depends(is_superuser())],
    **delete_role_schema,
)
@logger.info(os.path.basename(__file__))
async def delete(
    role_id: int,
    role_service: RoleService = Depends(get_role_service),
):
    deleted_role = await role_service.delete(role_id)
    return deleted_role


@router.post(
    "/assign",
    response_model=UserWithRoleResponseV1,
    dependencies=[Depends(is_superuser())],
    **assign_role_schema,
)
@logger.info(os.path.basename(__file__))
async def assign(
    user_email: str,
    role_name: str,
    user_role_service: UserRoleService = Depends(get_user_role_service),
):
    user_with_role = await user_role_service.assign(user_email, role_name)
    return user_with_role


@router.post(
    "/unassign",
    dependencies=[Depends(is_superuser())],
    **unassign_role_schema,
)
@logger.info(os.path.basename(__file__))
async def unassign(
    user_email: str,
    role_name: str,
    user_role_service: UserRoleService = Depends(get_user_role_service),
):
    user_with_role = await user_role_service.unassign(user_email, role_name)
    return user_with_role

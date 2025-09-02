import os

from fastapi import APIRouter, Depends, Request, status

from auth_lib.utils import get_token_from_request
from auth_service.src.api.swagger import (
    change_credentials_schema,
    login_history_schema,
    login_schema,
    logout_schema,
    refresh_schema,
    register_schema,
)
from auth_service.src.core import logger
from auth_service.src.schemas.auth.users import (
    UserCredentialsRequest,
    UserUpdateCredentials,
)
from auth_service.src.services.auth.auth import AuthService, get_auth_service
from auth_service.src.services.auth.users import UserService, get_user_service

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    **register_schema,
)
@logger.info(os.path.basename(__file__))
async def register(
    request: UserCredentialsRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.register(request)
    return {"message": "User registered"}


@router.post("/login", **login_schema)
@logger.info(os.path.basename(__file__))
async def login(
    login_data: UserCredentialsRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    login_result = await auth_service.login(login_data, request)
    return login_result


@router.post("/refresh", **refresh_schema)
@logger.info(os.path.basename(__file__))
async def refresh(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token = get_token_from_request(request)

    refresh_data = await auth_service.refresh(refresh_token)
    return refresh_data


@router.get("/user", **refresh_schema)
@logger.info(os.path.basename(__file__))
async def get_user_data(
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    token = get_token_from_request(request)

    user_data = await user_service.get_user_data(token)
    return user_data


@router.get("/user/roles", **refresh_schema)
@logger.info(os.path.basename(__file__))
async def get_user_roles(
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    token = get_token_from_request(request)

    user_roles = await user_service.get_user_roles(token)
    return user_roles


@router.post("/logout", **logout_schema)
@logger.info(os.path.basename(__file__))
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token = get_token_from_request(request)

    await auth_service.logout(access_token, request)
    return {"message": "Successfully logged out"}


@router.put("/change-credentials", **change_credentials_schema)
@logger.info(os.path.basename(__file__))
async def change_credentials(
    user_credentials: UserUpdateCredentials,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token = get_token_from_request(request)

    result = await auth_service.change_credentials(
        access_token,
        user_credentials,
    )
    return result


@router.get("/login-history", **login_history_schema)
@logger.info(os.path.basename(__file__))
async def get_login_history(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    token = get_token_from_request(request)

    history = await auth_service.get_login_history(token)
    return [
        {
            "login_time": entry.login_time.isoformat(),
            "ip_address": entry.ip_address,
            "action": entry.action,
        }
        for entry in history
    ]

import os
import string
from functools import wraps
from secrets import choice as secrets_choice

from fastapi import HTTPException, Request, status

from auth_service.src.auth.auth import decode_token

ENVIRONMENT = os.getenv("ENVIRONMENT", "develop")


def get_user_from_request(request: Request):
    try:
        token = get_token_from_request(request)
        user = decode_token(token)
        return user
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        else:
            raise e


def get_token_from_request(request: Request) -> str:
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token format",
        )

    return token.split("Bearer ")[1]


def token_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if ENVIRONMENT == "develop":
            return await func(request, *args, **kwargs)

        user = get_user_from_request(request)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not authorized",
            )
        return await func(request, *args, **kwargs)

    return wrapper


def generate_random_string():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets_choice(alphabet) for _ in range(16))

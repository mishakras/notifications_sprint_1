from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from auth_service.src.auth import exceptions as exc
from auth_service.src.models.auth.db_models import User
from auth_service.src.utils.config import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def verify_token(token: str) -> Optional[User]:
    try:
        payload = jwt.decode(
            token,
            config["AUTH_SECRET_KEY"],
            algorithms=[config["AUTH_ALGORITHM"]],
        )
        email = payload.get("sub")

        if email is None:
            raise exc.InvalidTokenSignatureException()

        return email

    except JWTError:
        raise exc.InvalidTokenSignatureException()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


def create_token(
    data: dict,
    expires_delta: timedelta,
):
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta
        or timedelta(minutes=config["ACCESS_TOKEN_EXPIRED_MINUTES"])
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        config["AUTH_SECRET_KEY"],
        algorithm=config["AUTH_ALGORITHM"],
    )


def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            config["AUTH_SECRET_KEY"],
            config["AUTH_ALGORITHM"],
        )
        return payload
    except JWTError:
        raise exc.InvalidTokenSignatureException()

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from auth_service.src.schemas.auth.roles import RoleResponseV1


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    email: str
    hashed_password: str
    is_superuser: bool
    is_active: Optional[bool] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    last_login_at: Optional[datetime.datetime] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    hashed_password: str
    is_superuser: bool
    last_login_at: Optional[datetime.datetime] = None


class UserCredentialsRequest(BaseModel):
    email: EmailStr = Field(
        None,
        example="some@example.com",
        description="Your email address",
    )
    password: SecretStr = Field(
        ...,
        example="somepassword",
        description="Your password for verification",
    )


class UserUpdateCredentials(UserCredentialsRequest):
    old_password: SecretStr = Field(
        ...,
        example="oldpassword123",
        description="Old password for verification",
    )

    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True


class UserWithRoleResponseV1(BaseModel):
    email: str
    role: RoleResponseV1


class OAuthUserData(BaseModel):
    user_id: str | None
    email: str

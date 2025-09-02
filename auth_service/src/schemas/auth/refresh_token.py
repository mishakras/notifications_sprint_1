import datetime

from pydantic import BaseModel, ConfigDict


class RefreshTokenBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    refresh_token: str
    issued_at: datetime.datetime
    expires_at: datetime.datetime
    revoked: bool


class RefreshTokenCreate(RefreshTokenBaseModel):
    pass


class RefreshTokenUpdate(RefreshTokenBaseModel):
    pass

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SocialAccountBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    social_id: str
    social_name: str
    user_id: int


class SocialAccountCreate(SocialAccountBaseModel):
    pass


class SocialAccountUpdate(SocialAccountBaseModel):
    pass

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Role(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str


class RoleCreate(Role):
    pass


class RoleUpdate(Role):
    pass


class RoleResponseV1(Role):
    pass

import datetime
from typing import Optional

from pydantic import BaseModel


class HistoryBase(BaseModel):
    user_id: int
    login_time: datetime.datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action: str


class HistoryCreate(HistoryBase):
    pass


class HistoryUpdate(HistoryBase):
    pass

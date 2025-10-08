from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RecommendRequest(BaseModel):
    """Вход для /api/v1/recommendations/recommend.

    - user_id: UUID (422 при невалидном значении)
    - search_list: допустимые поля; может быть пустым
    """

    user_id: UUID
    search_list: list[Literal["directors", "actors", "writers", "genres"]] = []

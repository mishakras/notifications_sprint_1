# broadcasts/services/users.py
from __future__ import annotations

from typing import Any, Dict

import requests
from django.conf import settings


class UserNotFound(Exception):
    pass


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Получает профиль пользователя из внешнего auth-сервиса.
    Ожидается JSON с полями: first_name, last_name, email, phone ...
    """
    base = settings.AUTH_API_URL.rstrip("/")
    url = f"{base}/api/v1/users/{user_id}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 404:
        raise UserNotFound(user_id)
    resp.raise_for_status()
    return resp.json()

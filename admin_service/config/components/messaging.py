from __future__ import annotations

import os
from typing import Any, Mapping

# Этот компонент подключается через split-settings из config/settings.py.
# В settings.py заранее формируется словарь `config`. Здесь мы аккуратно
# читаем значения из него, а если его нет (например, при изолированном
# запуске файла), используем переменные окружения как fallback.

_CFG: Mapping[str, Any] = globals().get("config", {})  # type: ignore[assignment]


def _cfg(key: str, default: str) -> str:
    """Вернуть значение из config либо из окружения, либо default."""
    return str(_CFG.get(key, os.getenv(key, default)))


KAFKA_BOOTSTRAP_SERVERS = _cfg("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = _cfg("KAFKA_TOPIC", "notifications")
SCHEDULER_TIMEZONE = _cfg("SCHEDULER_TIMEZONE", "UTC")

"""
Django settings for config project.
"""

from __future__ import annotations

import os
from pathlib import Path

from split_settings.tools import include

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / "staticfiles"

# === Опциональная загрузка .env только локально ===
# Используйте ТОЛЬКО для разработки: export USE_DOTENV=1
if os.getenv("USE_DOTENV", "0") == "1":
    env_path = BASE_DIR / "config" / ".env"
    if env_path.exists():
        # импорт внутри блока, чтобы не тянуть зависимость в проде
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(env_path)

# === Источник правды — ТОЛЬКО переменные окружения ===
config: dict[str, str] = dict(os.environ)


def env_bool(name: str, default: bool = False) -> bool:
    raw = config.get(name, str(int(default)))
    return raw.lower() in {"1", "true", "yes", "on"}


def env_list_required(name: str) -> list[str]:
    raw = config[name]  # KeyError, если отсутствует
    return [item.strip() for item in raw.split(",") if item.strip()]


# Проверяем обязательные переменные (без дефолтов в коде)
REQUIRED = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "AUTH_API_URL",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
]
missing = [k for k in REQUIRED if not config.get(k)]
if missing:
    raise RuntimeError(
        "Missing required environment variables: " + ", ".join(missing),
    )

# === Split settings (внутренние модули читают dict `config`) ===
include(
    "components/database.py",
    "components/application.py",
    "components/internationalization.py",
    "components/localization.py",
    "components/messaging.py",
)

# === Core Django ===
DEBUG = env_bool("DEBUG", default=False)

SECRET_KEY = config["SECRET_KEY"]
ALLOWED_HOSTS = (
    ["*"]
    if config["ALLOWED_HOSTS"] == "*"
    else env_list_required("ALLOWED_HOSTS")
)

# INTERNAL_IPS не секрет — разрешим пустым быть и дадим разумный dev-fallback
_internal_ips_raw = config.get("INTERNAL_IPS", "")
INTERNAL_IPS = [
    ip.strip() for ip in _internal_ips_raw.split(",") if ip.strip()
] or ["127.0.0.1"]

AUTH_API_URL = config["AUTH_API_URL"]

# Static
STATIC_URL = "static/"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

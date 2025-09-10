from __future__ import annotations

import os
from django.apps import AppConfig


class BroadcastsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "broadcasts"

    def ready(self) -> None:
        if os.getenv("DISABLE_SCHEDULER", "0") == "1":
            return
        from .scheduler import start_scheduler

        start_scheduler()

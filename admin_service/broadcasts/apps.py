from django.apps import AppConfig
import os

class BroadcastsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "broadcasts"
    verbose_name = "Рассылки"

    def ready(self) -> None:
        if os.getenv("DISABLE_SCHEDULER", "0") == "1":
            return
        from .scheduler import start_scheduler
        start_scheduler()

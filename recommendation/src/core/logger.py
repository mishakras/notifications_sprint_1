import logging
from collections.abc import Callable
from functools import wraps

import logstash

from .config import settings


class Logger:
    def __init__(self):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(
            logstash.LogstashHandler(
                settings.logstash.host,
                settings.logstash.port,
                tags=[settings.logstash.tag],
                version=1,
            ),
        )

    def info(self, file_name: str):
        def decorator(function: Callable):
            @wraps(function)
            async def wrapper(*args, **kwargs):
                # Используем dict вместо ручной сборки JSON
                log_data_start = {
                    "service": self.settings.app.title,
                    "router": file_name,
                    "action": function.__name__,
                    "status": "start",
                }
                self.logger.info(log_data_start)

                result = await function(*args, **kwargs)

                log_data_finish = {
                    "service": self.settings.app.title,
                    "router": file_name,
                    "action": function.__name__,
                    "status": "finish",
                }
                self.logger.info(log_data_finish)
                return result

            return wrapper

        return decorator


logger = Logger()

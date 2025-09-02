import logging
from functools import wraps
from typing import Callable

import logstash


class Logger:
    def __init__(self, settings):
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
                self.logger.info(
                    '{"service":"'
                    + self.settings.app.title
                    + '","router":"'
                    + file_name
                    + '","action":"'
                    + function.__name__
                    + '","status":"start"}',
                )
                result = await function(*args, **kwargs)
                self.logger.info(
                    '{"service":"'
                    + self.settings.app.title
                    + '","router":"'
                    + file_name
                    + '","action":"'
                    + function.__name__
                    + '","status":"finish"}',
                )
                return result

            return wrapper

        return decorator

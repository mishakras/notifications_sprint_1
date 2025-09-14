import logging
import sys

from logstash import LogstashHandler
from src.core.config import settings


def setup_logger(name: str | None = None) -> logging.Logger:
    """Настройка логгера с Logstash."""

    _logger = logging.getLogger(name or "notification_worker")
    _logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    # Logstash handler
    try:
        logstash_handler = LogstashHandler(
            settings.logstash.host,
            settings.logstash.port,
            version=1,
            tags=[settings.logstash.tag],
        )
        _logger.addHandler(logstash_handler)
    except Exception as e:
        _logger.warning(f"Failed to setup Logstash: {e}")

    return _logger


logger = setup_logger()

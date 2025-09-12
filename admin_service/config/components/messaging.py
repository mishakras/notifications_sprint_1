# Значения берём из общего config, собранного в settings.py

KAFKA_BOOTSTRAP_SERVERS = config.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

KAFKA_TOPIC = config.get(
    "KAFKA_TOPIC",
    "notifications",
)

SCHEDULER_TIMEZONE = config.get(
    "SCHEDULER_TIMEZONE",
    "UTC",
)

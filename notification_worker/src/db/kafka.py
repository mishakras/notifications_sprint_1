from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from src.core import settings


async def create_kafka_consumer():
    consumer = AIOKafkaConsumer(
        settings.kafka.topic,
        bootstrap_servers=settings.kafka.server,
        group_id=settings.kafka.group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_records=10,
    )
    await consumer.start()
    return consumer


async def create_dlq_producer():
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka.server,
        retry_backoff_ms=500,
        request_timeout_ms=20000,
    )
    await producer.start()
    return producer

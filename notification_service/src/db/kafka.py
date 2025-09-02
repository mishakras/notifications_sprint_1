from aiokafka import AIOKafkaProducer

from notification_service.src.core import settings

producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global producer
    if producer is None:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka.server,
                retry_backoff_ms=500,
                request_timeout_ms=20000,
            )
            await producer.start()
        except Exception:
            raise
    return producer


async def close_producer():
    global producer
    if producer is not None:
        await producer.stop()
        producer = None

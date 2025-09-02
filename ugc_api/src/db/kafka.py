from aiokafka import AIOKafkaProducer
from app.src.core import logger, settings

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
            logger.info("Kafka producer connected")
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            raise
    return producer


async def close_producer():
    global producer
    if producer is not None:
        await producer.stop()
        producer = None
        logger.info("Kafka producer disconnected")

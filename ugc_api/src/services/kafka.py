from functools import lru_cache

from aiokafka import AIOKafkaProducer
from app.src.db import get_producer
from fastapi import Depends


class KafkaService:
    def __init__(self, producer=Depends(get_producer)):
        self.producer = producer

    async def set(self, topic: str, value: bytes, key: bytes) -> None:
        await self.producer.send_and_wait(topic=topic, key=key, value=value)


@lru_cache()
def get_kafka_service(
    producer: AIOKafkaProducer = Depends(get_producer),
) -> KafkaService:
    return KafkaService(producer)

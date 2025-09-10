from __future__ import annotations

import json
import logging
from typing import Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class _KafkaWrapper:
    """
    Ленивая обёртка вокруг KafkaProducer, чтобы не падать на импорте при
    старте Django (когда окружение Kafka ещё не готово).
    """

    def __init__(self) -> None:
        self._producer: Optional[Any] = None
        self._topic: str = getattr(
            settings,
            "KAFKA_TOPIC",
            "notifications-topic",
        )
        self._bootstrap: str = getattr(
            settings,
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092",
        )
        self._import_error: Optional[Exception] = None

    def _ensure(self) -> None:
        """Лениво создаёт KafkaProducer один раз."""
        if self._producer or self._import_error:
            return
        try:
            # ЛЕНИВЫЙ импорт здесь, а не на уровне модуля:
            from kafka import KafkaProducer  # type: ignore

            self._producer = KafkaProducer(
                bootstrap_servers=self._bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
                linger_ms=10,
            )
            logger.info(
                "KafkaProducer initialized (bootstrap=%s, topic=%s)",
                self._bootstrap,
                self._topic,
            )
        except Exception as exc:  # noqa: BLE001
            # Запоминаем ошибку, чтобы поднять её при фактической отправке.
            self._import_error = exc
            logger.exception("Failed to initialize KafkaProducer")

    def publish(self, payload: dict[str, Any]) -> None:
        """Публикует сообщение в Kafka (тема берётся из настроек)."""
        self._ensure()
        if self._import_error:
            raise RuntimeError(
                "Kafka недоступна: проверь пакет kafka-python/six или "
                "переключись на REST-режим."
            ) from self._import_error

        assert self._producer is not None
        logger.debug(
            "Sending message to Kafka (topic=%s, keys=%s)",
            self._topic,
            list(payload.keys()),
        )
        self._producer.send(self._topic, value=payload)
        self._producer.flush(timeout=5)
        logger.info("Message sent to Kafka (topic=%s)", self._topic)

    def close(self) -> None:
        if self._producer:
            try:
                self._producer.close()
                logger.info("KafkaProducer closed")
            finally:
                self._producer = None


_kafka = _KafkaWrapper()


def publish_broadcast(
    *,
    campaign_id: int,
    template_id: int,
    delivery_method: str,
    audience: str,
) -> None:
    """Отправка задания на рассылку (транспорт: Kafka)."""
    payload: dict[str, Any] = {
        "user_id": "",
        "template_id": str(template_id),
        "notif_type": "broadcast",
        "email_params": None,
        "audience": audience,
        "delivery_method": delivery_method,
        "campaign_id": campaign_id,
    }
    _kafka.publish(payload)

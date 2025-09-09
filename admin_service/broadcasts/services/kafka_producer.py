# admin_service/broadcasts/services/kafka_producer.py
from __future__ import annotations

import json
from typing import Any, Optional

from django.conf import settings


class _KafkaWrapper:
    """Ленивая обёртка вокруг KafkaProducer, чтобы не падать на импорте при старте Django."""

    def __init__(self) -> None:
        self._producer = None
        self._topic: str = getattr(settings, "KAFKA_TOPIC", "notifications-topic")
        self._bootstrap: str = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._import_error: Optional[Exception] = None

    def _ensure(self) -> None:
        if self._producer or self._import_error:
            return
        try:
            # ЛЕНИВЫЙ импорт здесь, а не на уровне модуля
            from kafka import KafkaProducer  # type: ignore

            self._producer = KafkaProducer(
                bootstrap_servers=self._bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
                linger_ms=10,
            )
        except Exception as exc:  # noqa: BLE001
            # Запомним ошибку — будем поднимать её только при фактической отправке
            self._import_error = exc

    def publish(self, payload: dict[str, Any]) -> None:
        self._ensure()
        if self._import_error:
            raise RuntimeError(
                "Kafka недоступна: проверь пакет kafka-python/six или переключись на REST-режим."
            ) from self._import_error

        assert self._producer is not None
        self._producer.send(self._topic, value=payload)
        self._producer.flush(timeout=5)

    def close(self) -> None:
        if self._producer:
            self._producer.close()


_kafka = _KafkaWrapper()


def publish_broadcast(*, campaign_id: int, template_id: int, delivery_method: str, audience: str) -> None:
    """Отправка задания на рассылку (транспорт: Kafka)."""
    payload = {
        "user_id": "",
        "template_id": str(template_id),
        "notif_type": "broadcast",
        "email_params": None,
        "audience": audience,
        "delivery_method": delivery_method,
        "campaign_id": campaign_id,
    }
    _kafka.publish(payload)

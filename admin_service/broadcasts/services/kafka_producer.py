# admin_service/broadcasts/services/kafka_producer.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class _KafkaWrapper:
    """
    Ленивая обёртка вокруг KafkaProducer:
    - ждёт доступности брокера с ретраями;
    - перед отправкой пытается создать топик (idempotent).
    """

    def __init__(self) -> None:
        self._producer: Optional[Any] = None
        self._topic: str = getattr(settings, "KAFKA_TOPIC", "notifications")
        self._bootstrap: str = getattr(
            settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self._create_parts: int = int(
            getattr(settings, "KAFKA_TOPIC_PARTITIONS", 1)
        )
        self._create_repl: int = int(
            getattr(settings, "KAFKA_TOPIC_REPLICATION", 1)
        )
        self._connect_timeout: float = float(
            getattr(settings, "KAFKA_CONNECT_TIMEOUT", 30)
        )
        self._topic_ready: bool = False
        self._last_error: Optional[Exception] = None

    def _ensure(self) -> None:
        """Ленивая инициализация producer с ретраями + ensure_topic()."""
        if self._producer or self._last_error:
            return

        # Локальные импорты, чтобы не падать на старте Django
        try:
            from kafka import KafkaProducer  # type: ignore
            from kafka.admin import (  # type: ignore
                KafkaAdminClient,
                NewTopic,
            )
            from kafka.errors import (  # type: ignore
                NoBrokersAvailable,
                TopicAlreadyExistsError,
            )
        except Exception as exc:  # noqa: BLE001
            self._last_error = exc
            logger.exception("Kafka imports failed")
            return

        deadline = time.monotonic() + self._connect_timeout
        backoff = 0.5

        last_exc: Optional[Exception] = None
        while time.monotonic() < deadline:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self._bootstrap,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    retries=5,
                    linger_ms=10,
                )
                logger.info(
                    "KafkaProducer connected (bootstrap=%s, topic=%s)",
                    self._bootstrap,
                    self._topic,
                )
                # Попробуем создать топик (idempotent)
                if not self._topic_ready:
                    try:
                        admin = KafkaAdminClient(
                            bootstrap_servers=self._bootstrap
                        )
                        new_topics = [
                            NewTopic(
                                name=self._topic,
                                num_partitions=self._create_parts,
                                replication_factor=self._create_repl,
                            )
                        ]
                        admin.create_topics(
                            new_topics=new_topics, validate_only=False
                        )
                        admin.close()
                        logger.info(
                            "Kafka topic created: %s (p=%s, r=%s)",
                            self._topic,
                            self._create_parts,
                            self._create_repl,
                        )
                    except TopicAlreadyExistsError:
                        logger.debug(
                            "Kafka topic already exists: %s", self._topic
                        )
                    except Exception as exc:  # noqa: BLE001
                        # Не считаем это фатальной ошибкой для отправки
                        logger.warning("Topic create failed: %s", exc)
                    self._topic_ready = True
                return
            except NoBrokersAvailable as exc:
                last_exc = exc
            except Exception as exc:  # noqa: BLE001
                last_exc = exc

            time.sleep(backoff)
            backoff = min(5.0, backoff * 2)

        self._last_error = last_exc

    def publish(self, payload: dict[str, Any]) -> None:
        """Отправка сообщения в Kafka (с ленивой инициализацией)."""
        self._ensure()
        if self._last_error:
            raise RuntimeError(
                "Kafka недоступна: проверьте брокер и окружение."
            ) from self._last_error

        assert self._producer is not None
        logger.debug("Kafka send topic=%s keys=%s", self._topic, list(payload))
        self._producer.send(self._topic, value=payload)
        self._producer.flush(timeout=5)

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

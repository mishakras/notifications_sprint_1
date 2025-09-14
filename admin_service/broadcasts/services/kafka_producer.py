from __future__ import annotations

import json
import logging
import time
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class _KafkaWrapper:
    """
    Ленивая обёртка вокруг KafkaProducer.

    Нужна, чтобы не падать на импорте при старте Django, когда окружение
    Kafka ещё не готово.
    """

    def __init__(self) -> None:
        self._producer: Any | None = None
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
        self._startup_timeout: int = int(
            getattr(settings, "KAFKA_STARTUP_TIMEOUT", 60),
        )
        self._import_error: Exception | None = None

    def _ensure(self) -> None:
        """
        Лениво создаёт KafkaProducer один раз, с ретраями и
        автосозданием топика.
        """
        if self._producer or self._import_error:
            return

        try:
            # ленивые импорты — только когда реально понадобилось
            from kafka import KafkaProducer  # type: ignore
            from kafka.admin import KafkaAdminClient, NewTopic  # type: ignore
            from kafka.errors import (  # type: ignore
                NoBrokersAvailable,
                TopicAlreadyExistsError,
            )

            # ждём, пока брокеры поднимутся (экспоненциальный backoff)
            deadline = time.time() + self._startup_timeout
            backoff = 0.5
            last_err: Exception | None = None

            while time.time() < deadline:
                try:
                    self._producer = KafkaProducer(
                        bootstrap_servers=self._bootstrap,
                        value_serializer=lambda v: json.dumps(v).encode(
                            "utf-8",
                        ),
                        retries=5,
                        linger_ms=10,
                    )
                    logger.info(
                        "KafkaProducer initialized (bootstrap=%s, topic=%s)",
                        self._bootstrap,
                        self._topic,
                    )
                    break
                except NoBrokersAvailable as e:
                    last_err = e
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 5.0)
                except Exception as e:  # noqa: BLE001
                    # любая иная ошибка — подождём, но залогируем
                    last_err = e
                    logger.warning("Kafka init attempt failed: %s", e)
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 5.0)

            if self._producer is None:
                raise last_err or RuntimeError(
                    "KafkaProducer could not be created",
                )

            # проверяем/создаём топик
            admin: Any | None = None
            try:
                admin = KafkaAdminClient(
                    bootstrap_servers=self._bootstrap,
                )
                topic = NewTopic(
                    name=self._topic,
                    num_partitions=1,
                    replication_factor=1,
                )
                admin.create_topics(
                    new_topics=[topic],
                    validate_only=False,
                )
                logger.info("Kafka topic created: %s", self._topic)
            except TopicAlreadyExistsError:
                logger.debug("Kafka topic already exists: %s", self._topic)
            except Exception as e:  # noqa: BLE001
                # не критично для публикации — только предупредим
                logger.warning("Topic ensure failed: %s", e)
            finally:
                if admin is not None:
                    try:
                        admin.close()
                    except Exception:  # noqa: BLE001
                        pass

        except Exception as exc:  # noqa: BLE001
            self._import_error = exc
            logger.exception("Failed to initialize KafkaProducer")

    def publish(self, payload: dict[str, Any]) -> None:
        """Публикует сообщение в Kafka (тема берётся из настроек)."""
        self._ensure()
        if self._import_error:
            raise RuntimeError(
                "Kafka недоступна: проверь пакет kafka-python/six "
                "или переключись на REST-режим.",
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

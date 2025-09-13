import asyncio
import json

from src.core import logger
from src.db.kafka import create_dlq_producer
from src.services.auth.client import auth_client
from src.services.email_service.sender import email_sender
from src.utils.shortener import url_shortener
from src.utils.template_engine import template_engine


class NotificationProcessor:
    def __init__(self):
        self.dlq_producer = None
        self.dlq_topic = "notifications_dlq"

    async def initialize(self):
        self.dlq_producer = await create_dlq_producer()

    async def process_message(self, message: dict):
        """Обработка одного сообщения из Kafka"""
        try:
            # Получение данных пользователя
            user_data = await auth_client.get_user_data(message["user_id"])
            if not user_data:
                logger.warning(f"User {message['user_id']} not found")
                await self.send_to_dlq(message, "USER_NOT_FOUND")
                return

            # Получение шаблона (в реальном проекте - из БД)
            template = await self.get_template(message["template_id"])
            if not template:
                logger.warning(f"Template {message['template_id']} not found")
                await self.send_to_dlq(message, "TEMPLATE_NOT_FOUND")
                return

            # Подготовка контекста для шаблона
            context = {
                "user": user_data,
                "params": message.get("email_params", {}),
            }

            # Рендеринг шаблона
            subject = template_engine.render_template(
                template["subject"],
                context,
            )
            body = template_engine.render_template(template["body"], context)

            # Сокращение URL в тексте
            body = await url_shortener.process_urls_in_text(body)

            # Отправка уведомления
            success = await self.send_notification(
                user_data,
                subject,
                body,
                message.get("notif_type"),
            )

            if not success:
                await self.send_to_dlq(message, "SENDING_FAILED")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_to_dlq(message, "PROCESSING_ERROR")

    @staticmethod
    async def get_template(template_id: str) -> dict:
        """Получение шаблона уведомления"""
        # Заглушка - в реальном проекте получать из БД
        templates = {
            "welcome": {
                "subject": "Добро пожаловать, {{ user.first_name }}!",
                "body": "Приветствуем вас в нашем сервисе, "
                "{{ user.first_name }} {{ user.last_name }}!",
            },
            "new_movie": {
                "subject": "Новый фильм: {{ params.movie_title }}",
                "body": "У нас вышел новый фильм '{{ params.movie_title }}'"
                "! Посмотрите его по ссылке: {{ params.movie_url }}",
            },
        }
        return templates.get(template_id)

    @staticmethod
    async def send_notification(
        user_data: dict,
        subject: str,
        body: str,
        notif_type: str,
    ) -> bool:
        """Отправка уведомления в зависимости от типа"""
        if notif_type == "email":
            return await email_sender.send_email(
                user_data["email"],
                subject,
                body,
            )
        elif notif_type == "sms":
            # Реализация отправки SMS
            logger.info(
                f"SMS {user_data.get('phone')}: {subject} - {body[:50]}...",
            )
            return True
        elif notif_type == "push":
            # Реализация push-уведомления
            logger.info(
                f"Push to {user_data['id']}: {subject} - {body[:50]}...",
            )
            return True
        else:
            logger.warning(f"Unknown notification type: {notif_type}")
            return False

    async def send_to_dlq(self, message: dict, reason: str):
        """Отправка сообщения в Dead Letter Queue"""
        if self.dlq_producer:
            dlq_message = {
                "original_message": message,
                "reason": reason,
                "timestamp": asyncio.get_event_loop().time(),
            }
            await self.dlq_producer.send(
                self.dlq_topic,
                json.dumps(dlq_message).encode("utf-8"),
            )
            logger.warning(f"Message sent to DLQ: {reason}")


notification_processor = NotificationProcessor()

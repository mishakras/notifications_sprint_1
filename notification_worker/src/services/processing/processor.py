import asyncio
import json

from src.core import logger, settings
from src.core.constants import Environment
from src.db.kafka import create_dlq_producer
from src.services.auth.client import auth_client
from src.services.email_service.sender import email_sender
from src.services.push.sender import push_sender
from src.services.sms.sender import sms_sender
from src.utils.shortener import url_shortener
from src.utils.template_engine import template_engine


class NotificationProcessor:
    def __init__(self):
        self.dlq_producer = None
        self.dlq_topic = settings.kafka.dlq_topic

    async def initialize(self):
        self.dlq_producer = await create_dlq_producer()

        if settings.environment == Environment.DEVELOPMENT:
            email_test = await email_sender.test_connection()
            if email_test:
                logger.info("Email service connected successfully")
            else:
                logger.warning("Email service connection failed")

    async def process_message(
        self,
        message,
    ):
        try:
            logger.info(
                (
                    f"Processing message for user {message['user_id']}",
                    f", template {message['template_id']}",
                ),
            )

            user_data = await auth_client.get_user_data(message["user_id"])
            if not user_data:
                logger.warning(f"User {message['user_id']} not found")
                await self.send_to_dlq(message, "USER_NOT_FOUND")
                return

            template = await self.get_template(message["template_id"])
            if not template:
                logger.warning(
                    (
                        f"Template {message['template_id']} ",
                        "not found, using fallback",
                    ),
                )
                template = await self.get_fallback_template(
                    message.get(
                        "notif_type",
                        "email",
                    ),
                )

            context = await self.prepare_template_context(
                user_data,
                message,
            )

            subject = template_engine.render_template(
                template["subject"],
                context,
            )
            body = template_engine.render_template(
                template["body"],
                context,
            )

            body = await url_shortener.process_urls_in_text(body)

            notif_type = message.get(
                "notif_type",
                template["notification_type"],
            )

            success = await self.send_notification(
                user_data,
                subject,
                body,
                notif_type,
            )

            if success:
                logger.info(
                    (
                        "Notification sent successfully",
                        f" to user {message['user_id']}",
                    ),
                )
            else:
                logger.error(
                    (
                        "Failed to send notification ",
                        f"to user {message['user_id']}",
                    ),
                )
                await self.send_to_dlq(message, "SENDING_FAILED")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_to_dlq(message, "PROCESSING_ERROR")

    @staticmethod
    async def prepare_template_context(
        user_data,
        message,
    ):
        return {
            "user": {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "username": user_data.get("username"),
            },
            "params": message.get("email_params", {}),
            "system": {"environment": settings.environment},
        }

    @staticmethod
    async def get_template(template_id):
        templates = {
            "welcome": {
                "subject": "Добро пожаловать, {{ user.first_name }}!",
                "body": (
                    "Приветствуем вас в нашем сервисе, ",
                    "{{ user.first_name }} {{ user.last_name }}!",
                ),
                "notification_type": "email",
            },
            "new_movie": {
                "subject": "Новый фильм: {{ params.movie_title }}",
                "body": (
                    "У нас вышел новый фильм '{{ params.movie_title }}",
                    "'! Посмотрите его по ",
                    "ссылке: {{ params.movie_url }}",
                ),
                "notification_type": "email",
            },
        }
        return templates.get(template_id)

    @staticmethod
    async def get_fallback_template(template_type):
        fallback_templates = {
            "email": {
                "subject": "Уведомление от сервиса",
                "body": "Здравствуйте! Это уведомление от нашего сервиса.",
                "notification_type": "email",
            },
            "sms": {
                "subject": "",
                "body": "Уведомление от сервиса",
                "notification_type": "sms",
            },
            "push": {
                "subject": "Уведомление",
                "body": "Уведомление от сервиса",
                "notification_type": "push",
            },
        }
        return fallback_templates.get(
            template_type, fallback_templates["email"],
        )

    @staticmethod
    async def send_notification(
        user_data,
        subject,
        body,
        notif_type,
    ):
        try:
            if notif_type == "email" and user_data.get("email"):
                return await email_sender.send_email(
                    user_data["email"], subject, body,
                )

            elif notif_type == "sms" and user_data.get("phone"):
                return await sms_sender.send_sms(user_data["phone"], body)

            elif notif_type == "push":
                return await push_sender.send_push(
                    user_data["id"], subject, body,
                )

            else:
                logger.warning(
                    (
                        "Unsupported notification type or ",
                        f"missing recipient: {notif_type}",
                    ),
                )
                return False

        except Exception as e:
            logger.error(f"Error sending {notif_type} notification: {str(e)}")
            return False

    async def send_to_dlq(
        self,
        message,
        reason,
    ):
        if self.dlq_producer:
            dlq_message = {
                "original_message": message,
                "reason": reason,
                "timestamp": asyncio.get_event_loop().time(),
                "environment": settings.environment,
            }
            await self.dlq_producer.send(
                self.dlq_topic, json.dumps(dlq_message).encode("utf-8"),
            )
            logger.warning(f"Message sent to DLQ: {reason}")


notification_processor = NotificationProcessor()

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from src.core import logger, settings
from src.core.constants import Environment


class EmailSender:
    def __init__(self):
        self.host = settings.email.host
        self.port = settings.email.port
        self.username = settings.email.username
        self.password = settings.email.password
        self.use_tls = settings.email.use_tls
        self.from_email = settings.email.from_email
        self.from_name = settings.email.from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
    ):
        """Отправка email с поддержкой MailHog/Mailpit"""
        try:
            message = MIMEMultipart()
            message["From"] = formataddr((self.from_name, self.from_email))
            message["To"] = to_email
            message["Subject"] = subject

            content_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, content_type, "utf-8"))

            # Для разработки с Mailpit не нужны учетные данные
            if settings.environment == Environment.DEVELOPMENT:
                await aiosmtplib.send(
                    message,
                    hostname=self.host,
                    port=self.port,
                    use_tls=False,
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=self.host,
                    port=self.port,
                    username=self.username if self.username else None,
                    password=self.password if self.password else None,
                    use_tls=self.use_tls,
                )

            logger.info(
                f"Email sent to {to_email} via {self.host}:{self.port}"
            )
            return True

        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending email to {to_email}: {str(e)}",
            )
            return False

    async def test_connection(self):
        """Тестирование подключения к SMTP серверу"""
        try:
            async with aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=(
                    self.use_tls
                    if settings.environment != Environment.DEVELOPMENT
                    else False
                ),
            ) as server:
                if (
                    settings.environment != Environment.DEVELOPMENT
                    and self.username
                    and self.password
                ):
                    await server.login(self.username, self.password)
                return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False


email_sender = EmailSender()

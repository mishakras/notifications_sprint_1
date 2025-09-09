from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from src.core import logger, settings


class EmailSender:
    def __init__(self):
        self.host = settings.email.host
        self.port = settings.email.port
        self.username = settings.email.username
        self.password = settings.email.password
        self.use_tls = settings.email.use_tls

    async def send_email(
        self, to_email: str, subject: str, body: str, is_html: bool = False
    ):
        """Отправка email"""
        if not self.username or not self.password:
            logger.warning("Email credentials not configured")
            return False

        try:
            message = MIMEMultipart()
            message["From"] = self.username
            message["To"] = to_email
            message["Subject"] = subject

            content_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, content_type))

            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
            )

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False


email_sender = EmailSender()

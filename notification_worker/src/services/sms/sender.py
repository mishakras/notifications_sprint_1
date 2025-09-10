from src.core import logger


class SMSSender:
    def __init__(self):
        # Конфигурация SMS провайдера
        self.api_key = None  # Будет из настроек
        self.api_url = "https://sms-provider.com/api/send"

    @staticmethod
    async def send_sms(phone_number: str, message: str) -> bool:
        """Отправка SMS сообщения"""
        if not phone_number:
            logger.warning("Phone number not provided for SMS")
            return False

        try:
            # Заглушка - в реальном проекте интеграция с SMS провайдером
            logger.info(f"SMS to {phone_number}: {message[:50]}...")

            return True  # Заглушка для демонстрации

        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
            return False


sms_sender = SMSSender()

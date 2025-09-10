import aiohttp
from src.core import logger, settings


class AuthClient:
    def __init__(self):
        self.base_url = settings.auth.url
        self.timeout = aiohttp.ClientTimeout(total=settings.auth.timeout)

    async def get_user_data(self, user_id: str):
        """Получение данных пользователя из сервиса авторизации"""
        url = f"{self.base_url}/api/v1/users/{user_id}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"User {user_id} not found")
                        return None
                    else:
                        logger.error(f"Auth service error: {response.status}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Auth client error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in auth client: {str(e)}")
            return None

    async def get_user_preferences(self, user_id: str):
        """Получение предпочтений пользователя по уведомлениям"""
        url = f"{self.base_url}/api/v1/users/{user_id}/preferences"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(
                            f"User preferences not found for {user_id}",
                        )
                        return {
                            "email": True,
                            "sms": False,
                            "push": True,
                        }  # Default
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {"email": True, "sms": False, "push": True}


auth_client = AuthClient()

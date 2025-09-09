import aiohttp
from src.core import logger, settings


class URLShortener:
    def __init__(self):
        self.base_url = settings.shortener_url

    async def shorten_url(self, original_url: str) -> str:
        """Сокращение URL через сервис сокращения ссылок."""

        if not original_url:
            return original_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/shorten",
                    json={"url": original_url},
                    timeout=10,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return (
                            f"{self.base_url}/"
                            f"{result['short_url'].split('/')[-1]}"
                        )
                    else:
                        logger.warning(
                            f"Shortener service error: {response.status}"
                        )
                        return original_url
        except Exception as e:
            logger.error(f"URL shortening error: {str(e)}")
            return original_url

    async def process_urls_in_text(self, text: str) -> str:
        """Поиск и сокращение URL в тексте."""

        import re

        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

        urls = re.findall(url_pattern, text)
        for url in urls:
            shortened = await self.shorten_url(url)
            text = text.replace(url, shortened)

        return text


url_shortener = URLShortener()

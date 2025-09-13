import asyncio
import json
import signal
import time
from contextlib import AsyncExitStack

from aiokafka import AIOKafkaConsumer

from src.core import logger, settings
from src.core.constants import Environment
from src.db.kafka import create_kafka_consumer
from src.db.redis import close_redis, get_redis
from src.services.processing.processor import notification_processor


class NotificationWorker:
    def __init__(self):
        self.consumer = None
        self.redis = None
        self.running = False
        self.exit_stack = AsyncExitStack()

    async def start(self):
        logger.info(
            (
                "Starting notification worker in ",
                f"{settings.environment} environment...",
            ),
        )

        try:
            await self._initialize_dependencies()
            self._setup_signal_handlers()

            logger.info("Notification worker started successfully")
            await self._process_messages()

        except Exception as e:
            logger.error(f"Worker failed to start: {str(e)}")
            raise
        finally:
            await self.shutdown()

    async def _initialize_dependencies(self):
        self.consumer = await self.exit_stack.enter_async_context(
            await create_kafka_consumer(),
        )
        self.redis = await get_redis()
        await notification_processor.initialize()

        if settings.environment == Environment.DEVELOPMENT:
            logger.info("Development mode: Using Mailpit for email testing")
            logger.info(f"Mailpit UI: http://localhost:8025")
            logger.info(f"Kafka: {settings.kafka.server}")
            logger.info(f"Auth service: {settings.auth.url}")

        self.running = True

    def _setup_signal_handlers(self):
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.stop)

    async def _process_messages(self):
        async for message in self.consumer:
            if not self.running:
                break

            try:
                message_data = json.loads(message.value.decode("utf-8"))
                logger.info(
                    (
                        f"Received message: {message_data['template_id']}",
                        f" for user {message_data['user_id']}",
                    ),
                )

                await self._process_with_retry(message_data, message)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON message: {e}")
                await self.consumer.commit()
            except Exception as e:
                logger.error(f"Unexpected error processing message: {str(e)}")
                continue

    async def _process_with_retry(
        self,
        message_data,
        kafka_message,
    ):
        start_time = time.time()

        for attempt in range(settings.max_retries):
            try:
                await notification_processor.process_message(message_data)
                await self.consumer.commit()

                processing_time = time.time() - start_time
                logger.info(
                    (
                        "Message processed successfully",
                        f" in {processing_time:.2f}s",
                    ),
                )
                break

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt == settings.max_retries - 1:
                    logger.error(
                        (
                            "Message failed after ",
                            f"{settings.max_retries} attempts",
                        ),
                    )
                    await self.consumer.commit()
                else:
                    await asyncio.sleep(settings.retry_delay * (attempt + 1))

    def stop(self):
        logger.info("Stopping notification worker...")
        self.running = False

    async def shutdown(self):
        logger.info("Shutting down notification worker...")

        try:
            await self.exit_stack.aclose()
            await close_redis()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

        logger.info("Notification worker stopped")


async def main():
    worker = NotificationWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())

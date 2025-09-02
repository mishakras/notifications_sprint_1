import uuid

from app.src.core import logger, settings
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorCursor,
)


class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(settings.mongo.database_url)
            self.db = self.client[settings.mongo.name]
            await self.db.command("ping")
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise

    async def close(self):
        if self.client is not None:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"MongoDB closing error: {e}")
            finally:
                self.client = None
                self.db = None

    def _get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get collection."""
        return self.db[collection_name]

    @staticmethod
    def _patch_uuid(data: dict) -> dict:
        for key, value in data.items():
            if isinstance(value, uuid.UUID):
                data[key] = str(value)
        return data

    async def insert(
        self,
        collection_name: str,
        data: dict,
    ) -> None:
        """Insert data in mongoDB."""
        collection = self._get_collection(collection_name)
        await collection.insert_one(data)
        return None

    async def get_records(
        self,
        collection_name: str,
        condition: dict,
    ) -> AsyncIOMotorCursor:
        """Read data from mongoDB."""
        collection = self._get_collection(collection_name)
        return collection.find(self._patch_uuid(condition))

    async def get_record(
        self,
        collection_name: str,
        condition: dict,
    ) -> dict:
        """Read item from mongoDB."""
        collection = self._get_collection(collection_name)
        return await collection.find_one(self._patch_uuid(condition))

    async def delete(
        self,
        collection_name: str,
        condition: dict,
    ) -> None:
        """Delete from mongoDB."""
        collection = self._get_collection(collection_name)
        await collection.delete_many(self._patch_uuid(condition))


mongo_db = MongoDB()

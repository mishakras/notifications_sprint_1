import uuid
from datetime import datetime, timezone

import pytest_asyncio
from app.src.core import settings
from app.src.main import app
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient


async def insert_in_db(test_data, topic):
    client = AsyncIOMotorClient(settings.db.database_url)
    db = client[settings.db.name]
    collection = db[topic]
    await collection.insert_one(test_data)
    client.close()


@pytest_asyncio.fixture(scope="session")
def test_client():
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def test_page_view_data():
    topic = settings.topic.page_views["topic"]
    test_data = {
        "user_id": str(uuid.uuid4()),
        "page_id": str(uuid.uuid4()),
        "page_url": "https://example.com",
        "page_type": "film",
        "duration_seconds": 120.5,
        "created_at": datetime.now(timezone.utc),
    }
    await insert_in_db(test_data, topic)
    return test_data


@pytest_asyncio.fixture
async def test_clicks_data():
    topic = settings.topic.clicks["topic"]
    test_data = {
        "user_id": str(uuid.uuid4()),
        "target_id": str(uuid.uuid4()),
        "page_url": "https://example1.com",
        "target_type": "button",
        "created_at": datetime.now(timezone.utc),
    }
    await insert_in_db(test_data, topic)
    return test_data


@pytest_asyncio.fixture
async def test_search_filter_data():
    topic = settings.topic.search_filter_usages["topic"]
    test_data = {
        "user_id": str(uuid.uuid4()),
        "filter_type": "genre",
        "filter_value": "action",
        "search_query": "best action movies",
        "created_at": datetime.now(timezone.utc),
    }
    await insert_in_db(test_data, topic)
    return test_data


@pytest_asyncio.fixture
async def test_video_completion_data():
    topic = settings.topic.video_completions["topic"]
    test_data = {
        "user_id": str(uuid.uuid4()),
        "film_id": str(uuid.uuid4()),
        "duration": 120.5,
        "watched_percentage": 85.0,
        "created_at": datetime.now(timezone.utc),
    }
    await insert_in_db(test_data, topic)
    return test_data


@pytest_asyncio.fixture
async def test_video_quality_data():
    topic = settings.topic.video_quality_changes["topic"]
    test_data = {
        "user_id": str(uuid.uuid4()),
        "film_id": str(uuid.uuid4()),
        "from_quality": "480p",
        "to_quality": "1080p",
        "created_at": datetime.now(timezone.utc),
    }
    await insert_in_db(test_data, topic)
    return test_data

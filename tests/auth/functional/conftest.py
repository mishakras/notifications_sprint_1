from typing import Optional

import aiohttp
import pytest_asyncio
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from auth_service.src.auth.auth import hash_password
from auth_service.src.models.auth.db_models import User
from tests.auth.functional.settings import test_settings

REGISTER_ROUTE = "auth/register/"
LOGIN_ROUTE = "auth/login/"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPass123!"


@pytest_asyncio.fixture()
async def db_session():
    engine = create_async_engine(
        test_settings.get_connection_string(),
        echo=True,
    )
    session_maker = sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture()
async def aiohttp_session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture
def make_post_request(aiohttp_session):
    async def inner(
        api_route: str,
        body: dict[str, str],
        headers: Optional[dict[str, str]] = None,
    ):
        async with aiohttp_session.post(
            api_route,
            json=body,
            headers=headers,
        ) as response:
            if response.status == status.HTTP_204_NO_CONTENT:
                return response.status, None
            return response.status, await response.json()

    return inner


@pytest_asyncio.fixture(name="remove_test_user_if_exists")
async def remove_test_user_if_exists(db_session: AsyncSession):
    async def inner(email: str):
        query = select(User).filter(User.email == email)
        result = await db_session.execute(query)
        user_for_deletion = result.scalars().first()
        if user_for_deletion:
            await db_session.delete(user_for_deletion)
            await db_session.commit()
            await db_session.flush()

    return inner


@pytest_asyncio.fixture(name="create_test_user")
def create_test_user(db_session: AsyncSession, remove_test_user_if_exists):
    async def inner():
        await remove_test_user_if_exists(TEST_USER_EMAIL)
        user = User(
            email=TEST_USER_EMAIL,
            hashed_password=hash_password(TEST_USER_PASSWORD),
        )
        db_session.add(user)
        await db_session.commit()

    return inner

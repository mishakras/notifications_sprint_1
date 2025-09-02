import pytest
from fastapi import status

from tests.auth.functional.conftest import (
    LOGIN_ROUTE,
    REGISTER_ROUTE,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)
from tests.auth.functional.settings import test_settings


@pytest.mark.parametrize(
    ("user_data", "expected_status"),
    [
        (
            {
                "email": "registertest@example.com",
                "password": "valid_pass1",
            },
            status.HTTP_201_CREATED,
        ),
        (
            {
                "email": "registertest@example.com",
                "password": "valid_pass1",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "email": "registertest",
                "password": "valid_pass1",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        ({}, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
@pytest.mark.asyncio
async def test_user_register(
    make_post_request,
    user_data,
    expected_status,
):
    # Register a new user
    response_status, _ = await make_post_request(
        f"{test_settings.service_url}{REGISTER_ROUTE}",
        user_data,
    )

    assert response_status == expected_status


@pytest.mark.parametrize(
    ("user_data", "expected_status"),
    [
        (
            {
                "email": "unknownuser@example.com",
                "password": "invalid_pass1",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            },
            status.HTTP_200_OK,
        ),
    ],
)
@pytest.mark.asyncio
async def test_user_login(
    create_test_user,
    make_post_request,
    user_data,
    expected_status,
):
    # Create test a new user
    await create_test_user()

    # Test login
    response_status, _ = await make_post_request(
        f"{test_settings.service_url}{LOGIN_ROUTE}",
        user_data,
    )

    assert response_status == expected_status

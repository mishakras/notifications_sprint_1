import uuid
from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_get_user_filter_usages_current_data_success(
    test_client,
    test_search_filter_data,
):
    user_id = test_search_filter_data["user_id"]
    response = test_client.get(f"/api/v1/search_filter/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_filter_usages_no_data_success(test_client):
    user_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/search_filter/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_filter_type_usages_current_data_success(
    test_client,
    test_search_filter_data,
):
    filter_type = test_search_filter_data["filter_type"]
    response = test_client.get(f"/api/v1/search_filter/type/{filter_type}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data[0]["filter_type"] == filter_type


@pytest.mark.asyncio
async def test_get_filter_type_usages_no_data_success(test_client):
    filter_type = "non_existent_type"
    response = test_client.get(f"/api/v1/search_filter/type/{filter_type}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_user_filter_type_usage_correct_data_success(
    test_client,
    test_search_filter_data,
):
    user_id = test_search_filter_data["user_id"]
    filter_type = test_search_filter_data["filter_type"]
    response = test_client.get(
        f"/api/v1/search_filter/user_type/{user_id}/{filter_type}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["filter_value"] == "action"


@pytest.mark.asyncio
async def test_get_user_filter_type_usage_correct_data_exception_404(
    test_client,
):
    user_id = str(uuid.uuid4())
    filter_type = "non_existent_type"
    response = test_client.get(
        f"/api/v1/search_filter/user_type/{user_id}/{filter_type}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_user_filter_type_usage_correct_data_success(
    test_client,
    test_search_filter_data,
):
    user_id = test_search_filter_data["user_id"]
    filter_type = test_search_filter_data["filter_type"]
    response = test_client.delete(
        f"/api/v1/search_filter/remove/{user_id}/{filter_type}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        test_client.get(
            f"/api/v1/search_filter/user_type/{user_id}/{filter_type}/",
        ).status_code
        == HTTPStatus.NOT_FOUND
    )


@pytest.mark.asyncio
async def test_remove_user_filter_type_usage_no_data_exception_404(
    test_client,
):
    user_id = str(uuid.uuid4())
    filter_type = "non_existent_type"
    response = test_client.delete(
        f"/api/v1/search_filter/remove/{user_id}/{filter_type}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

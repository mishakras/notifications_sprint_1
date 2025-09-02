import uuid
from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_get_user_click_records_current_data_success(
    test_client,
    test_clicks_data,
):
    user_id = test_clicks_data["user_id"]
    response = test_client.get(f"/api/v1/click/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_click_records_no_data_success(test_client):
    user_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/click/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_target_click_records_current_data_success(
    test_client,
    test_clicks_data,
):
    target_id = test_clicks_data["target_id"]
    response = test_client.get(f"/api/v1/click/target/{target_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data[0]["target_id"] == target_id


@pytest.mark.asyncio
async def test_get_target_click_records_no_data_success(test_client):
    target_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/click/target/{target_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_user_target_click_records_correct_data_success(
    test_client,
    test_clicks_data,
):
    user_id = test_clicks_data["user_id"]
    target_id = test_clicks_data["target_id"]
    response = test_client.get(
        f"/api/v1/click/user_target/{user_id}/{target_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["page_url"] == "https://example1.com"


@pytest.mark.asyncio
async def test_get_user_target_click_records_correct_data_exception_404(
    test_client,
):
    user_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    response = test_client.get(
        f"/api/v1/click/user_target/{user_id}/{target_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_user_target_click_record_correct_data_success(
    test_client,
    test_clicks_data,
):
    user_id = test_clicks_data["user_id"]
    target_id = test_clicks_data["target_id"]
    response = test_client.delete(
        f"/api/v1/click/remove/{user_id}/{target_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        test_client.get(
            f"/api/v1/click/user_target/{user_id}/{target_id}/",
        ).status_code
        == HTTPStatus.NOT_FOUND
    )


@pytest.mark.asyncio
async def test_remove_user_target_click_record_no_data_exception_404(
    test_client,
):
    target_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    response = test_client.delete(
        f"/api/v1/click/remove/{user_id}/{target_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

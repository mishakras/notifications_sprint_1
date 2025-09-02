import uuid
from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_get_user_view_records_current_data_success(
    test_client,
    test_page_view_data,
):
    user_id = test_page_view_data["user_id"]
    response = test_client.get(f"/api/v1/page_view/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_view_records_no_data_success(test_client):
    user_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/page_view/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_page_view_records_current_data_success(
    test_client,
    test_page_view_data,
):
    page_id = test_page_view_data["page_id"]
    response = test_client.get(f"/api/v1/page_view/page/{page_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data[0]["page_id"] == page_id


@pytest.mark.asyncio
async def test_get_page_view_records_no_data_success(test_client):
    page_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/page_view/page/{page_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_user_page_view_records_correct_data_success(
    test_client,
    test_page_view_data,
):
    user_id = test_page_view_data["user_id"]
    page_id = test_page_view_data["page_id"]
    response = test_client.get(
        f"/api/v1/page_view/user_page/{user_id}/{page_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["page_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_user_page_view_records_correct_data_exception_404(
    test_client,
):
    page_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    response = test_client.get(
        f"/api/v1/page_view/user_page/{user_id}/{page_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_user_page_view_record_correct_data_success(
    test_client,
    test_page_view_data,
):
    user_id = test_page_view_data["user_id"]
    page_id = test_page_view_data["page_id"]
    response = test_client.delete(
        f"/api/v1/page_view/remove/{user_id}/{page_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        test_client.get(
            f"/api/v1/page_view/user_page/{user_id}/{page_id}/",
        ).status_code
        == HTTPStatus.NOT_FOUND
    )


@pytest.mark.asyncio
async def test_remove_user_page_view_record_no_data_exception_404(test_client):
    page_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    response = test_client.delete(
        f"/api/v1/page_view/remove/{user_id}/{page_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

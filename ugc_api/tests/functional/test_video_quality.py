import uuid
from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_get_user_quality_changes_current_data_success(
    test_client,
    test_video_quality_data,
):
    user_id = test_video_quality_data["user_id"]
    response = test_client.get(f"/api/v1/video_quality/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_quality_changes_no_data_success(test_client):
    user_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/video_quality/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_film_quality_changes_current_data_success(
    test_client,
    test_video_quality_data,
):
    film_id = test_video_quality_data["film_id"]
    response = test_client.get(f"/api/v1/video_quality/film/{film_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data[0]["film_id"] == film_id


@pytest.mark.asyncio
async def test_get_film_quality_changes_no_data_success(test_client):
    film_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/video_quality/film/{film_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_user_film_quality_change_correct_data_success(
    test_client,
    test_video_quality_data,
):
    user_id = test_video_quality_data["user_id"]
    film_id = test_video_quality_data["film_id"]
    response = test_client.get(
        f"/api/v1/video_quality/user_film/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["from_quality"] == "480p"


@pytest.mark.asyncio
async def test_get_user_film_quality_change_correct_data_exception_404(
    test_client,
):
    user_id = str(uuid.uuid4())
    film_id = str(uuid.uuid4())
    response = test_client.get(
        f"/api/v1/video_quality/user_film/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_user_film_quality_change_correct_data_success(
    test_client,
    test_video_quality_data,
):
    user_id = test_video_quality_data["user_id"]
    film_id = test_video_quality_data["film_id"]
    response = test_client.delete(
        f"/api/v1/video_quality/remove/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        test_client.get(
            f"/api/v1/video_quality/user_film/{user_id}/{film_id}/",
        ).status_code
        == HTTPStatus.NOT_FOUND
    )


@pytest.mark.asyncio
async def test_remove_user_film_quality_change_no_data_exception_404(
    test_client,
):
    user_id = str(uuid.uuid4())
    film_id = str(uuid.uuid4())
    response = test_client.delete(
        f"/api/v1/video_quality/remove/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

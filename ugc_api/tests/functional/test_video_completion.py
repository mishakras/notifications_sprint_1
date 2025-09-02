import uuid
from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_get_user_completions_current_data_success(
    test_client,
    test_video_completion_data,
):
    user_id = test_video_completion_data["user_id"]
    response = test_client.get(f"/api/v1/video_completion/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_completions_no_data_success(test_client):
    user_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/video_completion/user/{user_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_film_completions_current_data_success(
    test_client,
    test_video_completion_data,
):
    film_id = test_video_completion_data["film_id"]
    response = test_client.get(f"/api/v1/video_completion/film/{film_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data[0]["film_id"] == film_id


@pytest.mark.asyncio
async def test_get_film_completions_no_data_success(test_client):
    film_id = str(uuid.uuid4())
    response = test_client.get(f"/api/v1/video_completion/film/{film_id}/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_user_film_completion_correct_data_success(
    test_client,
    test_video_completion_data,
):
    user_id = test_video_completion_data["user_id"]
    film_id = test_video_completion_data["film_id"]
    response = test_client.get(
        f"/api/v1/video_completion/user_film/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["watched_percentage"] == 85.0


@pytest.mark.asyncio
async def test_get_user_film_completion_correct_data_exception_404(
    test_client,
):
    user_id = str(uuid.uuid4())
    film_id = str(uuid.uuid4())
    response = test_client.get(
        f"/api/v1/video_completion/user_film/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_user_film_completion_correct_data_success(
    test_client,
    test_video_completion_data,
):
    user_id = test_video_completion_data["user_id"]
    film_id = test_video_completion_data["film_id"]
    response = test_client.delete(
        f"/api/v1/video_completion/remove/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        test_client.get(
            f"/api/v1/video_completion/user_film/{user_id}/{film_id}/",
        ).status_code
        == HTTPStatus.NOT_FOUND
    )


@pytest.mark.asyncio
async def test_remove_user_film_completion_no_data_exception_404(test_client):
    user_id = str(uuid.uuid4())
    film_id = str(uuid.uuid4())
    response = test_client.delete(
        f"/api/v1/video_completion/remove/{user_id}/{film_id}/",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

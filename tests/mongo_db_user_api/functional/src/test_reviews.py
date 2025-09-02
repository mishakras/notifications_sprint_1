from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_create_review(make_post_request):
    create_resp = await make_post_request(
        endpoint="/api/v1/reviews/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
            "text": "Great job",
            "film_score_value": "5",
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]


@pytest.mark.asyncio
async def test_get_review(make_post_request, make_get_request):
    create_resp = await make_post_request(
        endpoint="/api/v1/reviews/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
            "text": "Great job",
            "film_score_value": "5",
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]

    review_id = create_resp["json"]["id"]

    get_resp = await make_get_request(
        endpoint=f"/api/v1/reviews/get/{review_id}",
    )
    assert get_resp["status"] == 200
    assert get_resp["json"]["text"] == "Great job"


@pytest.mark.asyncio
async def test_delete_review(
    make_post_request,
    make_get_request,
    make_delete_request,
):
    create_resp = await make_post_request(
        endpoint="/api/v1/reviews/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
            "text": "Great job",
            "film_score_value": "5",
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]

    review_id = create_resp["json"]["id"]

    get_resp = await make_get_request(
        endpoint=f"/api/v1/reviews/get/{review_id}",
    )
    assert get_resp["status"] == 200
    assert get_resp["json"]["text"] == "Great job"

    del_resp = await make_delete_request(
        endpoint=f"/api/v1/reviews/delete/{review_id}",
    )
    assert del_resp["status"] == 200


@pytest.mark.asyncio
async def test_add_like_review(make_post_request, make_get_request):
    create_resp = await make_post_request(
        endpoint="/api/v1/reviews/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
            "text": "Great job",
            "film_score_value": "5",
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]

    review_id = create_resp["json"]["id"]

    get_resp = await make_get_request(
        endpoint=f"/api/v1/reviews/get/{review_id}",
    )
    assert get_resp["status"] == 200
    assert get_resp["json"]["text"] == "Great job"

    add_like_resp = await make_post_request(
        endpoint=f"/api/v1/reviews/add_like/{review_id}",
        params={
            "like_score_value": "9",
            "user_id": uuid4().hex,
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert add_like_resp["status"] == 200

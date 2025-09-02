from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_create_film_mark(make_post_request):
    create_resp = await make_post_request(
        endpoint="/api/v1/film_marks/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]


@pytest.mark.asyncio
async def test_get_film_mark(make_post_request, make_get_request):
    create_resp = await make_post_request(
        endpoint="/api/v1/film_marks/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]

    film_mark_id = create_resp["json"]["id"]

    get_resp = await make_get_request(
        endpoint=f"/api/v1/film_marks/get/{film_mark_id}",
    )
    assert get_resp["status"] == 200


@pytest.mark.asyncio
async def test_delete_film_mark(
    make_post_request,
    make_get_request,
    make_delete_request,
):
    create_resp = await make_post_request(
        endpoint="/api/v1/film_marks/create",
        params={
            "film_id": uuid4().hex,
            "user_id": uuid4().hex,
        },
        headers={"Authorization": "Bearer test_token"},
    )
    assert create_resp["status"] == 200
    assert "id" in create_resp["json"]

    film_mark_id = create_resp["json"]["id"]

    get_resp = await make_get_request(
        endpoint=f"/api/v1/film_marks/get/{film_mark_id}",
    )
    assert get_resp["status"] == 200

    del_resp = await make_delete_request(
        endpoint=f"/api/v1/film_marks/delete/{film_mark_id}",
    )
    assert del_resp["status"] == 200

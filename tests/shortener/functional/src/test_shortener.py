import pytest


@pytest.mark.asyncio
async def test_shorten_and_redirect(make_post_request, make_get_request):
    url = "http://example.com"
    resp = await make_post_request(
        endpoint="/shorten",
        json={"url": url},
    )
    assert resp["status"] == 200
    short_path = resp["json"]["short_url"]
    assert short_path.startswith("/")

    redirect_resp = await make_get_request(
        endpoint=short_path,
        allow_redirects=False,
    )
    assert redirect_resp["status"] == 307
    assert redirect_resp["headers"]["location"] == url


@pytest.mark.asyncio
async def test_invalid_json(make_post_request):
    resp = await make_post_request(endpoint="/shorten", raw=True, data="")
    assert resp["status"] == 400
    assert "Invalid or missing JSON" in resp["json"]["detail"]


@pytest.mark.asyncio
async def test_unreachable_url(make_post_request):
    url = "http://nonexistent.subdomain.example.thisdomainshouldnotexist"
    resp = await make_post_request(endpoint="/shorten", json={"url": url})
    assert resp["status"] == 400
    assert "URL is not accessible or unsafe" in resp["json"]["detail"]


@pytest.mark.asyncio
async def test_private_ip_rejection(make_post_request):
    url = "http://127.0.0.1"
    resp = await make_post_request(endpoint="/shorten", json={"url": url})
    assert resp["status"] == 400
    assert "URL is not accessible or unsafe" in resp["json"]["detail"]

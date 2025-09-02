import ipaddress
import os
import shelve
import socket
import uuid

import httpx
import redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

USE_REDIS = bool(os.getenv("REDIS_URL"))
if USE_REDIS:
    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL"),
        decode_responses=True,
    )

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda redis_client, e: HTTPException(
        status_code=429,
        detail="Too many requests",
    ),
)

DB_FILE = "./db.db"


def generate_short_id() -> str:
    return uuid.uuid4().hex[:6]


def is_private_ip(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(host))
        except Exception:
            return True
    return ip.is_private or ip.is_loopback or ip.is_link_local


async def is_url_accessible(url: str, timeout: float = 3.0) -> bool:
    try:
        host = url.split("://", 1)[-1].split("/", 1)[0]
        if ".onion" in host or is_private_ip(host):
            return False
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.head(url)
            if response.status_code >= 400:
                response = await client.get(url)
            return response.status_code < 400
    except Exception:
        return False


def set_url(short_id: str, url: str):
    if USE_REDIS:
        redis_client.setex(short_id, 60 * 60 * 24 * 7, url)
    else:
        with shelve.open(DB_FILE) as db:
            db[short_id] = url


def get_url(short_id: str) -> str | None:
    if USE_REDIS:
        return redis_client.get(short_id)
    else:
        with shelve.open(DB_FILE) as db:
            return db.get(short_id)


@app.post("/shorten")
@limiter.limit("5/minute")
async def shorten(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing JSON body",
        )
    url = data.get("url")
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    if not await is_url_accessible(url):
        raise HTTPException(
            status_code=400,
            detail="URL is not accessible or unsafe",
        )

    short_id = generate_short_id()
    set_url(short_id, url)
    return {"short_url": f"/{short_id}"}


@app.get("/{short_id}")
async def redirect(short_id: str):
    url = get_url(short_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url)

# В самом верху conftest.py рядом с другими ENV
import os
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recommendation-tests")

import asyncio
import sys
from contextlib import asynccontextmanager

import docker
import pytest
from docker.errors import ImageNotFound
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from testcontainers.core.container import DockerContainer
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

ES_IMAGE = os.getenv("ES_IMAGE", "docker.elastic.co/elasticsearch/elasticsearch:8.17.0")
# Если вы на ARM/Mac M1/M2 и бывает путаница с платформой — раскомментируйте:
# os.environ.setdefault("DOCKER_DEFAULT_PLATFORM", "linux/amd64")



# <--- ВАЖНО: выставляем дефолты окружения ПЕРЕД import сервиса
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("ELASTIC_HOST", "http://localhost")
os.environ.setdefault("ELASTIC_PORT", "9200")
os.environ.setdefault("MONGO_DSN", "mongodb://localhost:27017/recommendation-tests")

# Добавляем корень репо в PYTHONPATH
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

@pytest.fixture(scope="session")
def anyio_backend():
    # чтобы pytest-asyncio/anyio не конфликтовали в окружении
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@asynccontextmanager
async def _ensure_es_ready(es):
    # ждём, пока кластер станет хотя бы yellow
    for _ in range(60):  # увеличили запас ожидания
        try:
            health = await es.cluster.health()
            if health.get("status") in ("yellow", "green"):
                break
        except Exception:
            pass
        await asyncio.sleep(1)
    yield


@pytest.fixture(scope="session")
def es_container():
    """
    Поднимаем Elasticsearch как DockerContainer.
    1) Пытаемся найти образ локально (без сети).
    2) Если нет — пробуем подтянуть.
    3) Если не вышло — скипаем тесты (инфраструктурная причина).
    """
    client = docker.from_env()

    # 1) Есть ли образ локально?
    try:
        client.images.get(ES_IMAGE)
    except ImageNotFound:
        # 2) Пробуем подтянуть из реестра
        try:
            client.images.pull(ES_IMAGE)
        except Exception as e:
            pytest.skip(f"Elasticsearch image '{ES_IMAGE}' недоступен: {e}")

    c = (
        DockerContainer(ES_IMAGE)
        .with_env("xpack.security.enabled", "false")
        .with_env("discovery.type", "single-node")
        .with_env("ES_JAVA_OPTS", "-Xms512m -Xmx512m")
        .with_exposed_ports(9200)
    )

    try:
        c.start()
        host = c.get_container_host_ip()
        port = int(c.get_exposed_port(9200))
        yield f"http://{host}:{port}"
    finally:
        c.stop()

@pytest.fixture(scope="session")
async def es_client(es_container) -> AsyncElasticsearch:
    url = es_container  # это уже http://host:port
    es = AsyncElasticsearch(hosts=[url], verify_certs=False)
    async with _ensure_es_ready(es):
        yield es
    await es.close()

@pytest.fixture(scope="session")
def mongo_container():
    with MongoDbContainer("mongo:7.0") as c:
        yield c


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7.2-alpine") as c:
        yield c



@pytest.fixture(scope="session")
async def redis_client(redis_container) -> Redis:
    host = redis_container.get_container_host_ip()
    try:
        port = int(redis_container.get_exposed_port("6379/tcp"))
    except Exception:
        port = int(redis_container.get_exposed_port(6379))

    r = Redis(host=host, port=port, decode_responses=True)

    # подождём готовность Redis
    for _ in range(30):
        try:
            pong = await r.ping()
            if pong:
                break
        except Exception:
            await asyncio.sleep(0.5)

    yield r
    await r.aclose()


@pytest.fixture(scope="session")
async def mongo_client(mongo_container) -> AsyncIOMotorClient:
    uri = mongo_container.get_connection_url()  # mongodb://host:port/db
    client = AsyncIOMotorClient(uri)
    # ensure
    for _ in range(30):
        try:
            await client.admin.command("ping")
            break
        except Exception:
            await asyncio.sleep(0.5)
    yield client
    client.close()


@pytest.fixture(scope="session", autouse=True)
async def wire_service_clients(es_client, redis_client, mongo_client):
    # Импорты сервиса откладываем сюда, когда env уже задано
    from recommendation.src.db import elastic as svc_elastic, redis as svc_redis, beanie as svc_beanie
    from recommendation.src.models.video_completion import VideoCompletionDB
    from beanie import init_beanie

    svc_elastic.es = es_client
    svc_redis.redis = redis_client
    svc_beanie.client = mongo_client

    await init_beanie(
        database=mongo_client[MONGO_DB_NAME],
        document_models=[VideoCompletionDB],  # оставьте ваш список моделей
    )
    yield



@pytest.fixture(scope="session", autouse=True)
async def seed_es(es_client):
    from recommendation.tests.testdata.schemas import IndexSchema
    from recommendation.tests.testdata.movies import data as MOVIES

    index_name = str(IndexSchema.MOVIES)

    # Enum -> dict
    schema = IndexSchema.MOVIES.value
    settings = schema.get("settings") or {}
    mappings = schema.get("mappings") or {}

    # создаём индекс (не падаем, если уже есть)
    await es_client.indices.create(
        index=index_name,
        settings=settings,
        mappings=mappings,
        ignore=400,
    )

    # bulk-загрузка фильмов
    actions = []
    for doc in MOVIES:
        actions += [{"index": {"_index": index_name, "_id": doc["id"]}}, doc]

    if actions:
        # в 8.x async-клиенте параметр называется operations=
        await es_client.bulk(operations=actions, refresh=True)

    yield

    # чистим после сессии
    await es_client.indices.delete(index=index_name, ignore=[400, 404])

@pytest.fixture(scope="session", autouse=True)
async def seed_mongo(mongo_client):
    db = mongo_client[MONGO_DB_NAME]
    coll = db["videocompletiondb"]

    # чистим коллекцию перед сидированием
    await coll.delete_many({})

    # подтягиваем тестовые данные истории просмотров
    try:
        # вариант для пакета с именем recommendation
        from recommendation.tests.testdata.history import data as HISTORY
    except Exception:
        try:
            # вариант, если тесты запускаются как tests/...
            from tests.recommendation.testdata.history import data as HISTORY
        except Exception:
            HISTORY = []

    # грузим, только если данные есть
    if HISTORY:
        await coll.insert_many(HISTORY)

    yield

    # чистим после прогона тестов
    await coll.delete_many({})

@pytest.fixture
def recommendation_service():
    from recommendation.src.services.recomendation_service import (
        RecommendationService,
        get_film_service,
        get_video_completion_service,
    )
    film_service = get_film_service()
    completion_service = get_video_completion_service()
    return RecommendationService(completion_service, film_service)

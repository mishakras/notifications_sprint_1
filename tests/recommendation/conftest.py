import asyncio
import os
import sys
from contextlib import asynccontextmanager

import docker
import pytest
from beanie import init_beanie
from docker.errors import ImageNotFound
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from testcontainers.core.container import DockerContainer
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer


ES_IMAGE = os.getenv(
    "ES_IMAGE",
    "docker.elastic.co/elasticsearch/elasticsearch:8.17.0",
)

os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("ELASTIC_HOST", "http://localhost")
os.environ.setdefault("ELASTIC_PORT", "9200")
os.environ.setdefault(
    "MONGO_DSN",
    "mongodb://localhost:27017/recommendation-tests",
)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recommendation-tests")

REPO_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    ),
)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture(scope="session")
def anyio_backend():
    """Совместимость с pytest-asyncio/anyio."""
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@asynccontextmanager
async def _ensure_es_ready(es_client: AsyncElasticsearch):
    """Дожидаемся статуса yellow/green."""
    for _ in range(60):
        try:
            health = await es_client.cluster.health()
            if health.get("status") in ("yellow", "green"):
                break
        except Exception:
            pass
        await asyncio.sleep(1)
    yield


@pytest.fixture(scope="session")
def es_container():
    """
    Поднимаем Elasticsearch через DockerContainer.
    Если образа нет — пытаемся загрузить; при неудаче — skip.
    """
    docker_client = docker.from_env()
    try:
        docker_client.images.get(ES_IMAGE)
    except ImageNotFound:
        try:
            docker_client.images.pull(ES_IMAGE)
        except Exception as exc:
            pytest.skip(
                f"Elasticsearch image '{ES_IMAGE}' недоступен: {exc}",
            )

    container = (
        DockerContainer(ES_IMAGE)
        .with_env("xpack.security.enabled", "false")
        .with_env("discovery.type", "single-node")
        .with_env("ES_JAVA_OPTS", "-Xms512m -Xmx512m")
        .with_exposed_ports(9200)
    )

    try:
        container.start()
        host = container.get_container_host_ip()
        port = int(container.get_exposed_port(9200))
        yield f"http://{host}:{port}"
    finally:
        container.stop()


@pytest.fixture(scope="session")
async def es_client(es_container) -> AsyncElasticsearch:
    es = AsyncElasticsearch(hosts=[es_container], verify_certs=False)
    async with _ensure_es_ready(es):
        yield es
    await es.close()


@pytest.fixture(scope="session")
def mongo_container():
    with MongoDbContainer("mongo:7.0") as container:
        yield container


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7.2-alpine") as container:
        yield container


@pytest.fixture(scope="session")
async def redis_client(redis_container) -> Redis:
    host = redis_container.get_container_host_ip()
    try:
        port = int(redis_container.get_exposed_port("6379/tcp"))
    except Exception:
        port = int(redis_container.get_exposed_port(6379))

    client = Redis(host=host, port=port, decode_responses=True)

    for _ in range(30):
        try:
            if await client.ping():
                break
        except Exception:
            await asyncio.sleep(0.5)

    yield client
    await client.aclose()


@pytest.fixture(scope="session")
async def mongo_client(mongo_container) -> AsyncIOMotorClient:
    uri = mongo_container.get_connection_url()
    client = AsyncIOMotorClient(uri)

    for _ in range(30):
        try:
            await client.admin.command("ping")
            break
        except Exception:
            await asyncio.sleep(0.5)

    yield client
    client.close()


@pytest.fixture(scope="session", autouse=True)
async def _wire_service_clients(es_client, redis_client, mongo_client):
    """
    Прокидываем реальные клиенты в модули сервиса и инициализируем
    beanie. Teardown не требуется.
    """
    from recommendation.src.db import beanie as svc_beanie
    from recommendation.src.db import elastic as svc_elastic
    from recommendation.src.db import redis as svc_redis
    from recommendation.src.models.video_completion import (
        VideoCompletionDB,
    )

    svc_elastic.es = es_client
    svc_redis.redis = redis_client
    svc_beanie.client = mongo_client

    await init_beanie(
        database=mongo_client[MONGO_DB_NAME],
        document_models=[VideoCompletionDB],
    )
    # ничего не возвращаем — фикстура только настраивает окружение


@pytest.fixture(scope="session", autouse=True)
async def _seed_es(es_client):
    """
    Сидируем тестовые фильмы в ES и удаляем индекс после сессии.
    """
    from recommendation.tests.testdata.movies import data as MOVIES
    from recommendation.tests.testdata.schemas import IndexSchema

    index_name = str(IndexSchema.MOVIES)
    schema = IndexSchema.MOVIES.value
    settings = schema.get("settings") or {}
    mappings = schema.get("mappings") or {}

    await es_client.indices.create(
        index=index_name,
        settings=settings,
        mappings=mappings,
        ignore=400,
    )

    actions = []
    for doc in MOVIES:
        actions.extend(
            [
                {"index": {"_index": index_name, "_id": doc["id"]}},
                doc,
            ],
        )

    if actions:
        await es_client.bulk(operations=actions, refresh=True)

    yield
    await es_client.indices.delete(index=index_name, ignore=[400, 404])


@pytest.fixture(scope="session", autouse=True)
async def _seed_mongo(mongo_client):
    """
    Сидируем историю просмотров и чистим коллекцию после сессии.
    """
    db = mongo_client[MONGO_DB_NAME]
    coll = db["videocompletiondb"]

    await coll.delete_many({})

    try:
        from recommendation.tests.testdata.history import data as HISTORY
    except Exception:
        try:
            from tests.recommendation.testdata.history import (
                data as HISTORY,
            )
        except Exception:
            HISTORY = []

    if HISTORY:
        await coll.insert_many(HISTORY)

    yield
    await coll.delete_many({})


@pytest.fixture
def recommendation_service():
    """
    Инстанс RecommendationService с зависимостями, уже «проваренными»
    выше через _wire_service_clients.
    """
    from recommendation.src.services.recomendation_service import (
        RecommendationService,
        get_film_service,
        get_video_completion_service,
    )

    film_service = get_film_service()
    completion_service = get_video_completion_service()
    return RecommendationService(completion_service, film_service)

from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from kafka import KafkaAdminClient
from kafka.admin import NewTopic

from notification_service.src.api.notif.v1 import notif
from notification_service.src.core import settings
from notification_service.src.db.kafka import close_producer, get_producer

app = FastAPI(
    title=settings.app.title,
    docs_url="/api/v1/openapi",
    openapi_url="/api/v1/openapi.json",
    default_response_class=ORJSONResponse,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@app.middleware("http")
async def before_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id")

    if not request_id:
        if settings.app.environment != "develop":
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        else:
            request_id = str(settings.app.zero_request_id)

    response = await call_next(request)

    response.headers["X-Request-Id"] = request_id
    return response


@app.on_event("startup")
async def startup():
    while True:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=settings.kafka.host
                + ":"
                + settings.kafka.port,
                api_version=(0, 9),
            )

            topic_list = []
            topic_list_exists = admin_client.list_topics()
            if "notifications" not in topic_list_exists:
                topic_list.append(
                    NewTopic(
                        name="notifications",
                        num_partitions=3,
                        replication_factor=2,
                    ),
                )
                admin_client.create_topics(
                    new_topics=topic_list,
                    validate_only=False,
                )
            break
        except:
            pass
    await get_producer()


@app.on_event("shutdown")
async def shutdown():
    await close_producer()


app.include_router(notif.router, prefix="/api/v1/notif", tags=["notif"])

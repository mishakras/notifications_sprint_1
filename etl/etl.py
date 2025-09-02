import logging
import signal
import time
from datetime import datetime
from typing import NoReturn

import elastic_transport
from dotenv import dotenv_values
from elastic import ElasticSupport
from states import DataProcessing
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)

default_envs = {
    "DB_HOST": "theatre-db",
    "DB_PORT": 5432,
    "ELASTIC_HOST": "elastic",
    "ELASTIC_PORT": 9200,
    "BATCH_SIZE": 100,
    "POSTGRES_DB": "theatre",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "secret",
    "LOG_FILE": "/var/log/etl_sync_service.log",
    "STORAGE_JSON_FILE": "/opt/storage.json",
    "INDEX_JSON_FILES": {
        "movies": "/opt/etl/common/es_movies_schema.json",
        "genres": "/opt/etl/common/es_genres_schema.json",
        "persons": "/opt/etl/common/es_persons_schema.json",
    },
    "RESYNC_TIMEOUT": 20,
    "DEFAULT_MODIFIED": datetime.strptime(
        "01-01-1970 00:00:00",
        "%m-%d-%Y %H:%M:%S",
    ),
}


config = {
    **default_envs,
    **dotenv_values("/opt/common/.env"),
}


logger = logging.getLogger(__name__)


logging.basicConfig(
    format="%(asctime)s %(message)s",
    filename=config["LOG_FILE"],
    encoding="utf-8",
    level=logging.DEBUG,
)


class GracefulKiller:
    def __init__(self) -> NoReturn:
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self) -> NoReturn:
        self.kill_now = True


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=30),
    stop=stop_after_delay(60),
    retry=retry_if_exception_type(elastic_transport.ConnectionError),
)
def indexes_sync(elastic_client: ElasticSupport):
    if not elastic_client.schema_exists:
        elastic_client.movies_index_check_or_create()


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=30),
    stop=stop_after_delay(60),
    retry=retry_if_exception_type(elastic_transport.ConnectionError),
)
def run_task_sync(
    elastic_client: ElasticSupport,
    data_processing: DataProcessing,
) -> NoReturn:
    for source in config["INDEX_JSON_FILES"]:
        for data in data_processing.retrieve_postgres_data(source):
            for item in data:
                data_processing.actualize_current_state(item, source)
            elastic_client.upload_data(data, source)


if __name__ == "__main__":
    logger.info("Start programm")
    killer = GracefulKiller()
    elastic_client = ElasticSupport(config)
    data_processing = DataProcessing(config)
    while not killer.kill_now:
        logger.info("Sync starting")
        indexes_sync(elastic_client)
        run_task_sync(elastic_client, data_processing)
        logger.info("Sync complete")
        time.sleep(config["RESYNC_TIMEOUT"])
    logger.info("Close programm")

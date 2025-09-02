import os
import time

import psycopg2
from psycopg2 import OperationalError

DB_LIST = [
    {
        "dbname": os.getenv("POSTGRES_DB", "theatre"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "secret"),
        "host": os.getenv("DB_HOST", "theatre-db"),
        "port": 5432,
    },
    {
        "dbname": os.getenv("AUTH_DB", "authservice"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "secret"),
        "host": os.getenv("DB_HOST", "theatre-db"),
        "port": 5432,
    },
]

RETRY_INTERVAL = 2


def wait_for_postgres_dbs():
    unavailable_dbs = {db["dbname"] for db in DB_LIST}
    while unavailable_dbs:
        for db_config in DB_LIST[:]:
            try:
                conn = psycopg2.connect(**db_config)
                conn.close()
                unavailable_dbs.discard(db_config["dbname"])
            except OperationalError:
                pass
        if unavailable_dbs:
            time.sleep(RETRY_INTERVAL)


if __name__ == "__main__":
    wait_for_postgres_dbs()

import os
import time
from datetime import datetime

import schedule
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

db_host = os.getenv("DB_HOST", "localhost")
db_user = os.getenv("POSTGRES_USER", "user")
db_password = os.getenv("POSTGRES_PASSWORD", "password")
db_name = os.getenv("AUTH_DB", "authservice")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def create_partition(year, month):
    partition_name = f"login_history_{year}_{month:02d}"
    partition_range_start = f"'{year}_{month:02d}-01'"
    partition_range_end = (
        f"'{year}_{month+1:02d}-01'" if month < 12 else f"'{year+1}-01-01'"
    )

    query = f"""
    CREATE TABLE IF NOT EXISTS {partition_name} PARTITION of login_history
    FOR VALUES FROM ({partition_range_start}) TO ({partition_range_end});
    """

    try:
        with Session() as session:
            session.execute(text(query))
            session.commit()
    except Exception as e:
        raise e


def partitioner():
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    create_partition(current_year, current_month)
    for future_delta in range(1, 6):
        future_year = current_year + ((current_month + future_delta - 1) // 12)
        future_month = (current_month + future_delta - 1) % 12 + 1
        create_partition(future_year, future_month)


if __name__ == "__main__":
    partitioner()
    schedule.every(2).minutes.do(partitioner)

    while True:
        schedule.run_pending()
        time.sleep(60)

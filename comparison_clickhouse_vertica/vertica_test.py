import random
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import vertica_python
from faker import Faker

fake = Faker()


class VerticaTestSuite:
    def __init__(
        self,
        host="localhost",
        port=5433,
        user="dbadmin",
        password="",
    ):
        self.connection_info = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": "VMart",
            "tlsmode": "disable",
        }

        self.target_schema = "test_schema"
        self.ensure_schema_exists()
        self.setup_table()

    def get_connection(self, database=None):
        """Получение соединения с базой данных"""
        conn_info = self.connection_info.copy()
        if database:
            conn_info["database"] = database
        conn_info["connection_timeout"] = 600
        conn_info["read_timeout"] = 600
        return vertica_python.connect(**conn_info)

    def ensure_schema_exists(self):
        """Создание тестовой схемы, если она не существует"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT schema_name FROM schemata WHERE schema_name = %s",
                    (self.target_schema,),
                )

                if not cursor.fetchone():
                    print(  # noqa: T201
                        f"Creating schema {self.target_schema}...",
                    )
                    cursor.execute(f"CREATE SCHEMA {self.target_schema}")
                    print(  # noqa: T201
                        f"Schema {self.target_schema} created successfully",
                    )
                else:
                    print(  # noqa: T201
                        f"Schema {self.target_schema} already exists",
                    )

        except Exception as e:
            print(f"Error ensuring schema exists: {e}")  # noqa: T201
            raise

    def setup_table(self):
        """Создание таблицы для тестирования"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    f"DROP TABLE IF EXISTS "
                    f"{self.target_schema}.user_activity_events",
                )

                create_sql = f"""
                    CREATE TABLE {self.target_schema}.user_activity_events
                    (
                        event_id              VARCHAR(36),
                        user_id               VARCHAR(36),
                        session_id            VARCHAR(36),
                        content_id            VARCHAR(36),
                        event_timestamp       TIMESTAMP NOT NULL,
                        event_type            VARCHAR(20),
                        event_duration        INTEGER,
                        progress_seconds      INTEGER,
                        quality_level         VARCHAR(10),
                        platform              VARCHAR(20),
                        user_region           VARCHAR(50),
                        content_type          VARCHAR(20),
                        content_category      VARCHAR(30),
                        user_subscription     VARCHAR(20),
                        bandwidth_mbps        FLOAT,
                        error_code            VARCHAR(10)
                    ) ORDER BY event_timestamp, user_id, content_id, event_type
                    SEGMENTED BY HASH(user_id) ALL NODES
                    PARTITION BY (DATE_TRUNC('month', event_timestamp)::DATE)
                """

                cursor.execute(create_sql)
                print("Vertica table created successfully")  # noqa: T201
        except Exception as e:
            print(f"Error creating table: {e}")  # noqa: T201
            raise

    def generate_batch_data(self, batch_size):
        """Генерация батча тестовых данных"""
        data = []
        event_types = [
            "content_view",
            "session_start",
            "session_end",
            "streaming",
            "pause",
            "resume",
            "error",
        ]
        quality_levels = ["240p", "480p", "720p", "1080p", "4K"]
        platforms = [
            "web",
            "mobile_ios",
            "mobile_android",
            "smart_tv",
            "tablet",
        ]
        regions = [
            "Moscow",
            "SPB",
            "Kazan",
            "Novosibirsk",
            "Yekaterinburg",
            "Rostov",
            "Samara",
        ]
        content_types = [
            "movie",
            "series",
            "documentary",
            "animation",
            "short",
        ]
        categories = [
            "action",
            "comedy",
            "drama",
            "thriller",
            "sci-fi",
            "romance",
            "horror",
        ]
        subscriptions = ["free", "basic", "premium", "family"]
        error_codes = [
            None,
            None,
            None,
            None,
            "E001",
            "E002",
            "E003",
        ]  # Больше null значений

        for _ in range(batch_size):
            event_type = random.choice(event_types)
            event_duration = (
                random.randint(1, 7200)
                if event_type in ["content_view", "streaming"]
                else random.randint(1, 300)
            )
            progress = (
                random.randint(0, event_duration)
                if event_type == "content_view"
                else 0
            )

            data.append(
                (
                    str(uuid4()),  # event_id
                    str(uuid4()),  # user_id
                    str(uuid4()),  # session_id
                    str(uuid4()),  # content_id
                    fake.date_time_between(start_date="-1y", end_date="now"),
                    event_type,
                    event_duration,
                    progress,
                    random.choice(quality_levels),
                    random.choice(platforms),
                    random.choice(regions),
                    random.choice(content_types),
                    random.choice(categories),
                    random.choice(subscriptions),
                    round(random.uniform(1.0, 100.0), 2),  # bandwidth_mbps
                    random.choice(error_codes),  # error_code
                ),
            )
        return data

    def insert_batch(self, batch_size, process_id):
        """Вставка одного батча данных"""
        start_time = time.time()
        data = self.generate_batch_data(batch_size)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            insert_sql = f"""
                INSERT INTO {self.target_schema}.user_activity_events
                (event_id, user_id, session_id, content_id, event_timestamp,
                 event_type, event_duration, progress_seconds, quality_level,
                 platform, user_region, content_type, content_category,
                 user_subscription, bandwidth_mbps, error_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)  # noqa: E501
            """

            cursor.executemany(insert_sql, data)
            conn.commit()

            end_time = time.time()
            duration = end_time - start_time
            print(  # noqa: T201
                f"Process {process_id}: Inserted {batch_size} records "
                f"in {duration:.2f} seconds",
            )
            return duration

    def test_insert_performance(
        self,
        total_records=10_000_000,
        batch_size=5000,
        num_processes=5,
    ):
        """Тестирование производительности вставки"""
        batches_per_process = total_records // (batch_size * num_processes)

        print(  # noqa: T201
            f"Starting insert test: {total_records} records, "
            f"batch size: {batch_size}, processes: {num_processes}",
        )
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_processes) as executor:
            futures = []
            for process_id in range(num_processes):
                for _ in range(batches_per_process):
                    future = executor.submit(
                        self.insert_batch,
                        batch_size,
                        process_id,
                    )
                    futures.append(future)

            for future in futures:
                future.result()

        end_time = time.time()
        total_time = end_time - start_time

        print("\nVertica Insert Performance Results:")  # noqa: T201
        print(f"Total records: {total_records}")  # noqa: T201
        print(f"Batch size: {batch_size}")  # noqa: T201
        print(f"Processes: {num_processes}")  # noqa: T201
        print(f"Total time: {total_time:.2f} seconds")  # noqa: T201
        print(  # noqa: T201
            f"Records per second: {total_records / total_time:.2f}",
        )

        return total_time

    def test_query_performance(self):
        """Тестирование производительности запросов"""
        queries = [
            # Анализ активности пользователей по месяцам
            (
                f"SELECT EXTRACT(YEAR FROM event_timestamp) * 100 + "
                f"EXTRACT(MONTH FROM event_timestamp) as month, event_type, "
                f"COUNT(*) as event_count FROM {self.target_schema}.user_activity_events "  # noqa: E501
                f"GROUP BY month, event_type ORDER BY month, event_count DESC"
            ),
            # Средняя продолжительность сессий по платформам
            (
                f"SELECT platform, AVG(event_duration) as avg_duration, "
                f"COUNT(DISTINCT session_id) as unique_sessions "
                f"FROM {self.target_schema}.user_activity_events "
                f"WHERE event_type = 'session_end' GROUP BY platform"
            ),
            # Топ контента по вовлеченности (прогресс просмотра)
            (
                f"SELECT content_id, content_category, "
                f"AVG(progress_seconds) as avg_progress, COUNT(*) as total_views "  # noqa: E501
                f"FROM {self.target_schema}.user_activity_events "
                f"WHERE event_type = 'content_view' "
                f"GROUP BY content_id, content_category "
                f"ORDER BY avg_progress DESC LIMIT 15"
            ),
            # Анализ качества стриминга по регионам
            (
                f"SELECT user_region, quality_level, "
                f"AVG(bandwidth_mbps) as avg_bandwidth, COUNT(*) as events "
                f"FROM {self.target_schema}.user_activity_events "
                f"WHERE event_type = 'streaming' "
                f"GROUP BY user_region, quality_level "
                f"ORDER BY avg_bandwidth DESC"
            ),
            # Сложный запрос: анализ ошибок и подписок за последний месяц
            (
                f"SELECT user_subscription, platform, COUNT(*) as error_count, "  # noqa: E501
                f"AVG(bandwidth_mbps) as avg_bandwidth "
                f"FROM {self.target_schema}.user_activity_events "
                f"WHERE event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days' "  # noqa: E501
                f"AND error_code IS NOT NULL "
                f"GROUP BY user_subscription, platform "
                f"ORDER BY error_count DESC LIMIT 25"
            ),
        ]

        results = []
        with self.get_connection() as conn:
            cursor = conn.cursor()

            for i, query in enumerate(queries, 1):
                start_time = time.time()
                cursor.execute(query)
                cursor.fetchall()
                end_time = time.time()

                query_time = end_time - start_time
                results.append(query_time)
                print(f"Query {i}: {query_time:.3f} seconds")  # noqa: T201

        return results


if __name__ == "__main__":
    vertica_test = VerticaTestSuite()

    batch_sizes = [1000, 5000, 10000]
    for batch_size in batch_sizes:
        print(f"\n=== Testing batch size: {batch_size} ===")  # noqa: T201
        vertica_test.setup_table()
        insert_time = vertica_test.test_insert_performance(
            total_records=5_000_000,
            batch_size=batch_size,
        )

        print("\n=== Query Performance Test ===")  # noqa: T201
        query_times = vertica_test.test_query_performance()
        avg_time = sum(query_times) / len(query_times)
        print(f"Average query time: {avg_time:.3f} seconds")  # noqa: T201

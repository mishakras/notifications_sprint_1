import random
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import clickhouse_connect
from faker import Faker

fake = Faker()


class ClickHouseTestSuite:
    def __init__(self, host="localhost", port=8123):
        self.host = host
        self.port = port
        self.client = None
        self.connect()
        self.setup_table()

    def connect(self):
        """Установка соединения с ClickHouse"""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username="default",
                password="",
            )
            self.client.query("SELECT 1")
            print(  # noqa: T201
                "ClickHouse connection established successfully",
            )
        except Exception as e:
            print(f"Failed to connect to ClickHouse: {e}")  # noqa: T201
            raise

    def setup_table(self):
        """Создание таблицы для тестирования"""
        try:
            drop_sql = "DROP TABLE IF EXISTS user_activity_events"
            create_sql = """
                         CREATE TABLE user_activity_events
                         (
                             event_id              UUID,
                             user_id               UUID,
                             session_id            UUID,
                             content_id            UUID,
                             event_timestamp       DateTime,
                             event_type            LowCardinality(String),
                             event_duration        UInt32,
                             progress_seconds      UInt32,
                             quality_level         LowCardinality(String),
                             platform              LowCardinality(String),
                             user_region           LowCardinality(String),
                             content_type          LowCardinality(String),
                             content_category      LowCardinality(String),
                             user_subscription     LowCardinality(String),
                             bandwidth_mbps        Float32,
                             error_code            Nullable(String)
                         ) ENGINE = MergeTree()
            ORDER BY (event_timestamp, user_id, content_id, event_type)
            PARTITION BY toYYYYMM(event_timestamp)
                         """

            self.client.command(drop_sql)
            self.client.command(create_sql)
            print("ClickHouse table created successfully")  # noqa: T201
        except Exception as e:
            print(f"Error creating ClickHouse table: {e}")  # noqa: T201
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
        error_codes = [None, None, None, None, "E001", "E002", "E003"]

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
                [
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
                ],
            )
        return data

    def insert_batch(self, batch_size, process_id):
        """Вставка одного батча данных"""
        start_time = time.time()
        data = self.generate_batch_data(batch_size)

        try:
            client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username="default",
                password="",
            )

            client.insert(
                "user_activity_events",
                data,
                column_names=[
                    "event_id",
                    "user_id",
                    "session_id",
                    "content_id",
                    "event_timestamp",
                    "event_type",
                    "event_duration",
                    "progress_seconds",
                    "quality_level",
                    "platform",
                    "user_region",
                    "content_type",
                    "content_category",
                    "user_subscription",
                    "bandwidth_mbps",
                    "error_code",
                ],
            )

            end_time = time.time()
            duration = end_time - start_time
            print(  # noqa: T201
                f"Process {process_id}: Inserted {batch_size} records "
                f"in {duration:.2f} seconds",
            )
            return duration
        except Exception as e:
            print(  # noqa: T201
                f"Error inserting batch for process {process_id}: {e}",
            )
            return 0

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

            total_insert_time = 0
            for future in futures:
                try:
                    insert_time = future.result()
                    total_insert_time += insert_time
                except Exception as e:
                    print(f"Error in future result: {e}")  # noqa: T201

        end_time = time.time()
        total_time = end_time - start_time

        print("\nClickHouse Insert Performance Results:")  # noqa: T201
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
                "SELECT toYYYYMM(event_timestamp) as month, event_type, "
                "COUNT(*) as event_count FROM user_activity_events "
                "GROUP BY month, event_type ORDER BY month, event_count DESC"
            ),
            # Средняя продолжительность сессий по платформам
            (
                "SELECT platform, AVG(event_duration) as avg_duration, "
                "COUNT(DISTINCT session_id) as unique_sessions "
                "FROM user_activity_events WHERE event_type = 'session_end' "
                "GROUP BY platform"
            ),
            # Топ контента по вовлеченности (прогресс просмотра)
            (
                "SELECT content_id, content_category, "
                "AVG(progress_seconds) as avg_progress, COUNT(*) as total_views "  # noqa: E501
                "FROM user_activity_events WHERE event_type = 'content_view' "
                "GROUP BY content_id, content_category "
                "ORDER BY avg_progress DESC LIMIT 15"
            ),
            # Анализ качества стриминга по регионам
            (
                "SELECT user_region, quality_level, "
                "AVG(bandwidth_mbps) as avg_bandwidth, COUNT(*) as events "
                "FROM user_activity_events WHERE event_type = 'streaming' "
                "GROUP BY user_region, quality_level "
                "ORDER BY avg_bandwidth DESC"
            ),
            # Сложный запрос: анализ ошибок и подписок за последний месяц
            (
                "SELECT user_subscription, platform, COUNT(*) as error_count, "
                "AVG(bandwidth_mbps) as avg_bandwidth FROM user_activity_events "  # noqa: E501
                "WHERE event_timestamp >= now() - INTERVAL 30 DAY "
                "AND error_code IS NOT NULL "
                "GROUP BY user_subscription, platform "
                "ORDER BY error_count DESC LIMIT 25"
            ),
        ]

        results = []
        for i, query in enumerate(queries, 1):
            try:
                start_time = time.time()
                self.client.query(query)
                end_time = time.time()

                query_time = end_time - start_time
                results.append(query_time)
                print(f"Query {i}: {query_time:.3f} seconds")  # noqa: T201
            except Exception as e:
                print(f"Error executing query {i}: {e}")  # noqa: T201
                results.append(0)

        return results


if __name__ == "__main__":
    try:
        ch_test = ClickHouseTestSuite()

        batch_sizes = [1000, 5000, 10000]
        for batch_size in batch_sizes:
            print(f"\n=== Testing batch size: {batch_size} ===")  # noqa: T201
            ch_test.setup_table()
            insert_time = ch_test.test_insert_performance(
                total_records=1_000_000,
                batch_size=batch_size,
            )

            print("\n=== Query Performance Test ===")  # noqa: T201
            query_times = ch_test.test_query_performance()
            avg_time = sum(query_times) / len(query_times)
            print(f"Average query time: {avg_time:.3f} seconds")  # noqa: T201
    except Exception as e:
        print(f"Error running ClickHouse tests: {e}")  # noqa: T201

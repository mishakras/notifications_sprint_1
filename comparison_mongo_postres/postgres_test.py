import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import timezone

import asyncpg
from faker import Faker
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

fake = Faker()


@dataclass
class TestResult:
    operation: str
    records_count: int
    batch_size: int
    duration: float
    records_per_second: float
    query_times: list[float] = None


class PostgreSQLTester:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Подключение к PostgreSQL"""
        try:
            connection_string = settings.pg_db.get_connection_string
            self.pool = await asyncpg.create_pool(
                connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            logger.info("Успешное подключение к PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return False

    async def create_tables(self):
        """Создание таблиц"""
        try:
            async with self.pool.acquire() as conn:
                # Создание таблицы лайков
                await conn.execute(  # noqa: E501
                    """
                    CREATE TABLE IF NOT EXISTS likes (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        movie_id INTEGER NOT NULL,
                        rating SMALLINT NOT NULL CHECK (rating >= 0 AND rating <= 10),  # noqa: E501
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        UNIQUE(user_id, movie_id)
                    )
                """,
                )

                # Создание таблицы рецензий
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reviews (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        movie_id INTEGER NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        rating SMALLINT NOT NULL CHECK (rating >= 0 AND rating <= 10),  # noqa: E501
                        likes_count INTEGER DEFAULT 0,
                        dislikes_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL
                    )
                """,
                )

                # Создание таблицы закладок
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bookmarks (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        movie_id INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        UNIQUE(user_id, movie_id)
                    )
                """,
                )

                logger.info("Таблицы успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")

    async def create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        try:
            async with self.pool.acquire() as conn:
                # Индексы для лайков
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_likes_movie_id ON likes(movie_id)",  # noqa: E501
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_likes_user_id ON likes(user_id)",  # noqa: E501
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_likes_created_at ON likes(created_at)",  # noqa: E501
                )

                # Индексы для рецензий
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews(movie_id)",  # noqa: E501
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id)",  # noqa: E501
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at)",  # noqa: E501
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reviews_likes_count ON reviews(likes_count DESC)",  # noqa: E501
                )

                # Индексы для закладок
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id)",  # noqa: E501
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at)",  # noqa: E501
                )

                logger.info("Индексы успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка создания индексов: {e}")

    async def clear_data(self):
        """Очистка всех данных"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "TRUNCATE TABLE likes, reviews, bookmarks RESTART IDENTITY",  # noqa: E501
                )
                logger.info("Данные очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")

    def generate_likes_data(self, count: int) -> list:
        """Генерация данных лайков"""
        likes = []
        for _ in range(count):
            like = (
                fake.random_int(min=1, max=1000000),  # user_id
                fake.random_int(min=1, max=100000),  # movie_id
                fake.random_int(min=0, max=10),  # rating
                fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),  # created_at
            )
            likes.append(like)
        return likes

    def generate_reviews_data(self, count: int) -> list:
        """Генерация данных рецензий"""
        reviews = []
        for _ in range(count):
            review = (
                fake.random_int(min=1, max=1000000),  # user_id
                fake.random_int(min=1, max=100000),  # movie_id
                fake.sentence(nb_words=6),  # title
                fake.text(max_nb_chars=2000),  # content
                fake.random_int(min=0, max=10),  # rating
                fake.random_int(min=0, max=1000),  # likes_count
                fake.random_int(min=0, max=100),  # dislikes_count
                fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),  # created_at
            )
            reviews.append(review)
        return reviews

    def generate_bookmarks_data(self, count: int) -> list:
        """Генерация данных закладок"""
        bookmarks = []
        for _ in range(count):
            bookmark = (
                fake.random_int(min=1, max=1000000),  # user_id
                fake.random_int(min=1, max=100000),  # movie_id
                fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),  # created_at
            )
            bookmarks.append(bookmark)
        return bookmarks

    async def insert_data_batch(
        self,
        table: str,
        data: list,
        batch_size: int,
    ) -> TestResult:
        """Вставка данных батчами"""
        start_time = time.time()
        total_inserted = 0

        try:
            async with self.pool.acquire() as conn:
                for i in range(0, len(data), batch_size):
                    batch = data[i : i + batch_size]  # noqa: E203

                    if table == "likes":
                        query = """
                            INSERT INTO likes
                            (user_id, movie_id, rating, created_at)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (user_id, movie_id) DO NOTHING
                        """
                    elif table == "reviews":
                        query = """
                            INSERT INTO reviews
                            (user_id, movie_id, title, content, rating,
                            likes_count, dislikes_count, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """
                    elif table == "bookmarks":
                        query = """
                            INSERT INTO bookmarks
                            (user_id, movie_id, created_at)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (user_id, movie_id) DO NOTHING
                        """

                    await conn.executemany(query, batch)
                    total_inserted += len(batch)

            duration = time.time() - start_time
            records_per_second = (
                total_inserted / duration if duration > 0 else 0
            )

            return TestResult(
                operation="insert",
                records_count=total_inserted,
                batch_size=batch_size,
                duration=duration,
                records_per_second=records_per_second,
            )
        except Exception as e:
            logger.error(f"Ошибка вставки данных в {table}: {e}")
            return None

    async def test_queries(self) -> list[float]:
        """Тестирование запросов на чтение"""
        query_times = []

        async with self.pool.acquire() as conn:
            # Запрос 1: Получение лайков пользователя
            start_time = time.time()
            _user_likes = await conn.fetch(  # noqa: F841
                "SELECT * FROM likes WHERE user_id = $1 LIMIT 100",
                12345,
            )
            query_times.append(time.time() - start_time)

            # Запрос 2: Подсчет лайков фильма
            start_time = time.time()
            _movie_likes_count = await conn.fetchval(  # noqa: F841
                "SELECT COUNT(*) FROM likes WHERE movie_id = $1",
                1001,
            )
            query_times.append(time.time() - start_time)

            # Запрос 3: Средняя оценка фильма
            start_time = time.time()
            _avg_rating = await conn.fetchval(  # noqa: F841
                "SELECT AVG(rating) FROM likes WHERE movie_id = $1",
                1001,
            )
            query_times.append(time.time() - start_time)

            # Запрос 4: Закладки пользователя
            start_time = time.time()
            _user_bookmarks = await conn.fetch(  # noqa: F841
                "SELECT * FROM bookmarks WHERE user_id = $1 LIMIT 100",
                12345,
            )
            query_times.append(time.time() - start_time)

            # Запрос 5: Популярные рецензии фильма
            start_time = time.time()
            _popular_reviews = await conn.fetch(  # noqa: F841
                """SELECT * FROM reviews
                   WHERE movie_id = $1
                   ORDER BY likes_count DESC LIMIT 10""",
                1001,
            )
            query_times.append(time.time() - start_time)

        return query_times

    async def run_performance_test(
        self,
        data_volume: int,
        batch_size: int,
    ) -> dict:
        """Запуск полного теста производительности"""
        logger.info(
            f"Начало теста: {data_volume} записей, batch_size: {batch_size}",
        )

        results = {
            "data_volume": data_volume,
            "batch_size": batch_size,
            "insert_results": {},
            "query_results": [],
        }

        # Очистка данных
        await self.clear_data()

        # Генерация и вставка лайков (70% от общего объема)
        likes_count = int(data_volume * 0.7)
        likes_data = self.generate_likes_data(likes_count)
        likes_result = await self.insert_data_batch(
            "likes",
            likes_data,
            batch_size,
        )
        if likes_result:
            results["insert_results"]["likes"] = {
                "duration": likes_result.duration,
                "records_per_second": likes_result.records_per_second,
                "records_count": likes_result.records_count,
            }

        # Генерация и вставка рецензий (20% от общего объема)
        reviews_count = int(data_volume * 0.2)
        reviews_data = self.generate_reviews_data(reviews_count)
        reviews_result = await self.insert_data_batch(
            "reviews",
            reviews_data,
            batch_size,
        )
        if reviews_result:
            results["insert_results"]["reviews"] = {
                "duration": reviews_result.duration,
                "records_per_second": reviews_result.records_per_second,
                "records_count": reviews_result.records_count,
            }

        # Генерация и вставка закладок (10% от общего объема)
        bookmarks_count = int(data_volume * 0.1)
        bookmarks_data = self.generate_bookmarks_data(bookmarks_count)
        bookmarks_result = await self.insert_data_batch(
            "bookmarks",
            bookmarks_data,
            batch_size,
        )
        if bookmarks_result:
            results["insert_results"]["bookmarks"] = {
                "duration": bookmarks_result.duration,
                "records_per_second": bookmarks_result.records_per_second,
                "records_count": bookmarks_result.records_count,
            }

        # Тестирование запросов
        for _ in range(settings.proj.test_iterations):
            query_times = await self.test_queries()
            results["query_results"].append(query_times)

        # Вычисление среднего времени запросов
        if results["query_results"]:
            avg_query_times = []
            for i in range(5):  # 5 типов запросов
                times = [result[i] for result in results["query_results"]]
                avg_query_times.append(sum(times) / len(times))
            results["avg_query_times"] = avg_query_times

        logger.info(
            f"Тест завершен: {data_volume} записей, batch_size: {batch_size}",
        )
        return results

    async def close(self):
        """Закрытие соединения"""
        if self.pool:
            await self.pool.close()
            logger.info("Соединение с PostgreSQL закрыто")


async def main():
    tester = PostgreSQLTester()

    if not await tester.connect():
        return

    await tester.create_tables()
    await tester.create_indexes()

    test_volumes = [100000, 1000000, 5000000, 10000000]
    test_batch_sizes = [1000, 5000, 10000, 25000, 50000, 100000]

    all_results = []

    for volume in test_volumes:
        for batch_size in test_batch_sizes:
            if batch_size <= volume:
                result = await tester.run_performance_test(volume, batch_size)
                all_results.append(result)

    # Сохранение результатов
    with open("postgresql_test_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Результаты сохранены в postgresql_test_results.json")

    await tester.close()


if __name__ == "__main__":
    asyncio.run(main())

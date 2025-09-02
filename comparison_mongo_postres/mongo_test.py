import json
import logging
import time
from dataclasses import dataclass
from datetime import timezone

import pymongo
from faker import Faker
from pymongo import IndexModel, MongoClient
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


class MongoDBTester:
    def __init__(self):
        self.client = None
        self.db = None
        self.likes_collection = None
        self.reviews_collection = None
        self.bookmarks_collection = None

    def connect(self):
        """Подключение к MongoDB"""
        try:
            connection_string = settings.mongo_db.get_connection_string
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
            )
            # Проверка подключения
            self.client.admin.command("ping")
            self.db = self.client[settings.mongo_db.database]

            # Получение коллекций
            self.likes_collection = self.db.likes
            self.reviews_collection = self.db.reviews
            self.bookmarks_collection = self.db.bookmarks

            logger.info("Успешное подключение к MongoDB")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            return False

    def create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        try:
            # Индексы для лайков
            likes_indexes = [
                IndexModel([("user_id", 1), ("movie_id", 1)], unique=True),
                IndexModel([("movie_id", 1)]),
                IndexModel([("user_id", 1)]),
                IndexModel([("created_at", 1)]),
            ]
            self.likes_collection.create_indexes(likes_indexes)

            # Индексы для рецензий
            reviews_indexes = [
                IndexModel([("movie_id", 1)]),
                IndexModel([("user_id", 1)]),
                IndexModel([("created_at", 1)]),
                IndexModel([("likes_count", -1)]),
            ]
            self.reviews_collection.create_indexes(reviews_indexes)

            # Индексы для закладок
            bookmarks_indexes = [
                IndexModel([("user_id", 1), ("movie_id", 1)], unique=True),
                IndexModel([("user_id", 1)]),
                IndexModel([("created_at", 1)]),
            ]
            self.bookmarks_collection.create_indexes(bookmarks_indexes)

            logger.info("Индексы успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка создания индексов: {e}")

    def clear_data(self):
        """Очистка всех данных"""
        try:
            self.likes_collection.delete_many({})
            self.reviews_collection.delete_many({})
            self.bookmarks_collection.delete_many({})
            logger.info("Данные очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")

    def generate_likes_data(self, count: int) -> list[dict]:
        """Генерация данных лайков"""
        likes = []
        for _ in range(count):
            like = {
                "user_id": fake.random_int(min=1, max=1000000),
                "movie_id": fake.random_int(min=1, max=100000),
                "rating": fake.random_int(min=0, max=10),
                "created_at": fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),
            }
            likes.append(like)
        return likes

    def generate_reviews_data(self, count: int) -> list[dict]:
        """Генерация данных рецензий"""
        reviews = []
        for _ in range(count):
            review = {
                "user_id": fake.random_int(min=1, max=1000000),
                "movie_id": fake.random_int(min=1, max=100000),
                "title": fake.sentence(nb_words=6),
                "content": fake.text(max_nb_chars=2000),
                "rating": fake.random_int(min=0, max=10),
                "likes_count": fake.random_int(min=0, max=1000),
                "dislikes_count": fake.random_int(min=0, max=100),
                "created_at": fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),
            }
            reviews.append(review)
        return reviews

    def generate_bookmarks_data(self, count: int) -> list[dict]:
        """Генерация данных закладок"""
        bookmarks = []
        for _ in range(count):
            bookmark = {
                "user_id": fake.random_int(min=1, max=1000000),
                "movie_id": fake.random_int(min=1, max=100000),
                "created_at": fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                    tzinfo=timezone.utc,
                ),
            }
            bookmarks.append(bookmark)
        return bookmarks

    def insert_data_batch(
        self,
        collection,
        data: list[dict],
        batch_size: int,
    ) -> TestResult:
        """Вставка данных"""
        start_time = time.time()
        total_inserted = 0

        try:
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]  # noqa:E203
                try:
                    collection.insert_many(batch, ordered=False)
                    total_inserted += len(batch)
                except pymongo.errors.BulkWriteError as e:
                    total_inserted += len(batch) - len(
                        e.details["writeErrors"],
                    )

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
            logger.error(f"Ошибка вставки данных: {e}")
            return None

    def test_queries(self) -> list[float]:
        """Тестирование запросов на чтение"""
        query_times = []

        # Запрос 1: Получение лайков пользователя
        start_time = time.time()
        _user_likes = list(  # noqa: F841
            self.likes_collection.find({"user_id": 12345}).limit(100),
        )
        query_times.append(time.time() - start_time)

        # Запрос 2: Подсчет лайков фильма
        start_time = time.time()
        _movie_likes_count = (  # noqa: F841
            self.likes_collection.count_documents(
                {"movie_id": 1001},
            )
        )
        query_times.append(time.time() - start_time)

        # Запрос 3: Средняя оценка фильма
        start_time = time.time()
        _avg_rating = list(  # noqa: F841
            self.likes_collection.aggregate(
                [
                    {"$match": {"movie_id": 1001}},
                    {
                        "$group": {
                            "_id": None,
                            "avg_rating": {"$avg": "$rating"},
                        },
                    },
                ],
            ),
        )
        query_times.append(time.time() - start_time)

        # Запрос 4: Закладки пользователя
        start_time = time.time()
        _user_bookmarks = list(  # noqa: F841
            self.bookmarks_collection.find({"user_id": 12345}).limit(100),
        )
        query_times.append(time.time() - start_time)

        # Запрос 5: Популярные рецензии фильма
        start_time = time.time()
        _popular_reviews = list(  # noqa: F841
            self.reviews_collection.find({"movie_id": 1001})
            .sort("likes_count", -1)
            .limit(10),
        )
        query_times.append(time.time() - start_time)

        return query_times

    def run_performance_test(self, data_volume: int, batch_size: int) -> dict:
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
        self.clear_data()

        # Генерация и вставка лайков (70% от общего объема)
        likes_count = int(data_volume * 0.7)
        likes_data = self.generate_likes_data(likes_count)
        likes_result = self.insert_data_batch(
            self.likes_collection,
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
        reviews_result = self.insert_data_batch(
            self.reviews_collection,
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
        bookmarks_result = self.insert_data_batch(
            self.bookmarks_collection,
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
            query_times = self.test_queries()
            results["query_results"].append(query_times)

        # Вычисление средних времен запросов
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

    def close(self):
        """Закрытие соединения"""
        if self.client:
            self.client.close()
            logger.info("Соединение с MongoDB закрыто")


def main():
    """Основная функция для запуска тестов"""
    tester = MongoDBTester()

    if not tester.connect():
        return

    # Создание индексов
    tester.create_indexes()

    # Запуск тестов для разных объемов данных и размеров батчей
    test_volumes = [100000, 1000000, 5000000, 10000000]
    test_batch_sizes = [1000, 5000, 10000, 25000, 50000, 100000]

    all_results = []

    for volume in test_volumes:
        for batch_size in test_batch_sizes:
            if batch_size <= volume:  # Батч не может быть больше общего объема
                result = tester.run_performance_test(volume, batch_size)
                all_results.append(result)

    # Сохранение результатов
    with open("mongodb_test_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Результаты сохранены в mongodb_test_results.json")

    tester.close()


if __name__ == "__main__":
    main()

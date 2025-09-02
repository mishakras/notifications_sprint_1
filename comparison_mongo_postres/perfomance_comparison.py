import asyncio
import json
import logging
from datetime import datetime

from mongo_test import MongoDBTester
from postgres_test import PostgreSQLTester
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PerformanceComparison:
    def __init__(self):
        self.mongo_tester = MongoDBTester()
        self.postgres_tester = PostgreSQLTester()
        self.results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "target_response_time": settings.proj.target_response_time,
                "test_iterations": settings.proj.test_iterations,
                "parallel_processes": settings.proj.num_processes,
            },
            "mongodb": [],
            "postgresql": [],
            "comparison": [],
        }

    async def setup_databases(self):
        """Настройка баз данных"""
        logger.info("Настройка MongoDB...")
        if not self.mongo_tester.connect():
            raise Exception("Не удалось подключиться к MongoDB")
        self.mongo_tester.create_indexes()

        logger.info("Настройка PostgreSQL...")
        if not await self.postgres_tester.connect():
            raise Exception("Не удалось подключиться к PostgreSQL")
        await self.postgres_tester.create_tables()
        await self.postgres_tester.create_indexes()

        logger.info("Базы данных настроены")

    def run_mongo_tests(
        self,
        test_volumes: list[int],
        test_batch_sizes: list[int],
    ):
        """Запуск тестов MongoDB"""
        logger.info("Запуск тестов MongoDB...")

        for volume in test_volumes:
            for batch_size in test_batch_sizes:
                if batch_size <= volume:
                    logger.info(
                        f"MongoDB тест: {volume} записей, batch {batch_size}",
                    )
                    result = self.mongo_tester.run_performance_test(
                        volume,
                        batch_size,
                    )
                    if result:
                        result["database"] = "mongodb"
                        self.results["mongodb"].append(result)

    async def run_postgres_tests(
        self,
        test_volumes: list[int],
        test_batch_sizes: list[int],
    ):
        """Запуск тестов PostgreSQL"""
        logger.info("Запуск тестов PostgreSQL...")

        for volume in test_volumes:
            for batch_size in test_batch_sizes:
                if batch_size <= volume:
                    logger.info(
                        f"PostgreSQL тест: {volume} записей, batch {batch_size}",  # noqa: E501
                    )
                    result = await self.postgres_tester.run_performance_test(  # noqa: E501
                        volume,
                        batch_size,
                    )
                    if result:
                        result["database"] = "postgresql"
                        self.results["postgresql"].append(result)

    def compare_results(self):  # noqa: CFQ001
        """Сравнение результатов"""
        logger.info("Сравнение результатов...")

        # Группировка результатов по объему данных и размеру батча
        mongo_results = {
            (r["data_volume"], r["batch_size"]): r
            for r in self.results["mongodb"]
        }
        postgres_results = {
            (r["data_volume"], r["batch_size"]): r
            for r in self.results["postgresql"]
        }

        for key in mongo_results.keys():
            if key in postgres_results:
                mongo_result = mongo_results[key]
                postgres_result = postgres_results[key]

                comparison = {
                    "data_volume": key[0],
                    "batch_size": key[1],
                    "insert_comparison": {},
                    "query_comparison": {},
                    "winner": {},
                }

                # Сравнение вставки данных
                for data_type in ["likes", "reviews", "bookmarks"]:
                    if (
                        data_type in mongo_result["insert_results"]
                        and data_type in postgres_result["insert_results"]
                    ):
                        mongo_rps = mongo_result["insert_results"][data_type][
                            "records_per_second"
                        ]
                        postgres_rps = postgres_result["insert_results"][
                            data_type
                        ]["records_per_second"]

                        comparison["insert_comparison"][data_type] = {
                            "mongodb_rps": mongo_rps,
                            "postgresql_rps": postgres_rps,
                            "ratio": (
                                mongo_rps / postgres_rps
                                if postgres_rps > 0
                                else 0
                            ),
                            "faster": (
                                "mongodb"
                                if mongo_rps > postgres_rps
                                else "postgresql"
                            ),
                        }

                # Сравнение запросов
                if (
                    "avg_query_times" in mongo_result
                    and "avg_query_times" in postgres_result
                ):
                    mongo_avg = sum(mongo_result["avg_query_times"]) / len(
                        mongo_result["avg_query_times"],
                    )
                    postgres_avg = sum(
                        postgres_result["avg_query_times"],
                    ) / len(postgres_result["avg_query_times"])

                    comparison["query_comparison"] = {
                        "mongodb_avg_time": mongo_avg,
                        "postgresql_avg_time": postgres_avg,
                        "ratio": (
                            postgres_avg / mongo_avg if mongo_avg > 0 else 0
                        ),
                        "faster": (
                            "mongodb"
                            if mongo_avg < postgres_avg
                            else "postgresql"
                        ),
                        "meets_target": {
                            "mongodb": mongo_avg
                            <= settings.proj.target_response_time,
                            "postgresql": postgres_avg
                            <= settings.proj.target_response_time,
                        },
                    }

                # Определение общего победителя
                insert_wins = sum(
                    1
                    for comp in comparison["insert_comparison"].values()
                    if comp["faster"] == "mongodb"
                )
                query_faster = comparison["query_comparison"].get("faster", "")

                if query_faster == "mongodb" and insert_wins >= 2:
                    comparison["winner"]["overall"] = "mongodb"
                elif query_faster == "postgresql" and insert_wins <= 1:
                    comparison["winner"]["overall"] = "postgresql"
                else:
                    comparison["winner"]["overall"] = "mixed"

                self.results["comparison"].append(comparison)

    def save_results(self):
        """Сохранение результатов"""
        with open(
            "results/comparison_results.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                self.results,
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        # Генерация отчета для вывода в консоль
        report_summary = self.generate_summary()
        logger.info("Сводка результатов:")
        logger.info(report_summary)

        logger.info("Результаты сохранены в results/comparison_results.json")

    def generate_summary(self):
        """Генерация краткой сводки результатов"""
        summary = []

        mongo_wins = sum(
            1
            for comp in self.results["comparison"]
            if comp["winner"]["overall"] == "mongodb"
        )
        postgres_wins = sum(
            1
            for comp in self.results["comparison"]
            if comp["winner"]["overall"] == "postgresql"
        )
        mixed_results = (
            len(self.results["comparison"]) - mongo_wins - postgres_wins
        )

        summary.append("\n=== ИТОГОВЫЕ РЕЗУЛЬТАТЫ СРАВНЕНИЯ ===")
        summary.append(f"MongoDB побед: {mongo_wins}")
        summary.append(f"PostgreSQL побед: {postgres_wins}")
        summary.append(f"Смешанные результаты: {mixed_results}\n")

        return "\n".join(summary)

    async def run_full_comparison(self):
        """Запуск полного сравнения"""
        try:
            await self.setup_databases()

            # Определение тестовых параметров
            test_volumes = [100000, 1000000, 5000000, 10000000]
            test_batch_sizes = [1000, 5000, 10000, 25000, 50000, 100000]

            # Запуск тестов
            self.run_mongo_tests(test_volumes, test_batch_sizes)
            await self.run_postgres_tests(test_volumes, test_batch_sizes)

            # Сравнение и сохранение результатов
            self.compare_results()
            self.save_results()

            logger.info("Сравнение завершено успешно")

        except Exception as e:
            logger.error(f"Ошибка при выполнении сравнения: {e}")
        finally:
            # Закрытие соединений
            self.mongo_tester.close()
            await self.postgres_tester.close()


async def main():
    comparison = PerformanceComparison()
    await comparison.run_full_comparison()


if __name__ == "__main__":
    asyncio.run(main())

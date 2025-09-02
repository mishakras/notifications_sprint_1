import json
import subprocess
import sys
import time
from datetime import datetime

import requests
import vertica_python
from clickhouse_test import ClickHouseTestSuite
from vertica_test import VerticaTestSuite


class PerformanceComparison:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "clickhouse": {},
            "vertica": {},
            "comparison": {},
        }

    def check_docker_containers(self):
        """Проверка запущенных Docker контейнеров"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "ps",
                    "--services",
                    "--filter",
                    "status=running",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            running_services = (
                result.stdout.strip().split("\n")
                if result.stdout.strip()
                else []
            )

            required_services = ["clickhouse", "vertica"]
            missing_services = [
                svc for svc in required_services if svc not in running_services
            ]

            if missing_services or not running_services:
                print("Starting Docker containers...")  # noqa: T201
                subprocess.run(["docker", "compose", "up", "-d"], check=True)
                print("Waiting for containers to start...")  # noqa: T201
                time.sleep(30)
                return True

            print("All required containers are already running")  # noqa: T201
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error with docker compose commands: {e}")  # noqa: T201
            print(  # noqa: T201
                "Make sure Docker Desktop is running and "
                "docker compose is available",
            )
            return False
        except FileNotFoundError:
            print(  # noqa: T201
                "Docker or docker compose not found. "
                "Please ensure Docker Desktop is installed and running.",
            )
            return False

    def wait_for_clickhouse(self, max_attempts=30):
        """Ожидание готовности ClickHouse"""
        print("Waiting for ClickHouse to be ready...")  # noqa: T201
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    "http://localhost:8123/ping",
                    timeout=5,
                )
                if response.status_code == 200:
                    print("ClickHouse is ready!")  # noqa: T201
                    return True
            except Exception as e:
                print(  # noqa: T201
                    f"Attempt {attempt + 1}/{max_attempts}: "
                    f"ClickHouse not ready - {e}",
                )
                time.sleep(5)

        print("ClickHouse failed to become ready")  # noqa: T201
        return False

    def wait_for_vertica(
        self,
        host="localhost",
        port=5433,
        user="dbadmin",
        password="",
        max_attempts=30,
    ):
        """Ожидание готовности Vertica"""
        print("Waiting for Vertica to be ready...")  # noqa: T201

        for attempt in range(max_attempts):
            try:
                conn_info = {
                    "host": host,
                    "port": port,
                    "user": user,
                    "password": password,
                    "tlsmode": "disable",
                }

                with vertica_python.connect(**conn_info) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()
                    version_str = version[0] if version else "Unknown"
                    print(  # noqa: T201
                        f"Vertica is ready! Version: {version_str}",
                    )
                    return True

            except Exception as e:
                print(  # noqa: T201
                    f"Attempt {attempt + 1}/{max_attempts}: "
                    f"Vertica not ready yet - {e}",
                )
                time.sleep(5)

        print("Vertica failed to become ready within timeout")  # noqa: T201
        return False

    def setup_environment(self):
        """Настройка тестовой среды"""
        print("=== Database Performance Comparison Setup ===")  # noqa: T201

        if not self.check_docker_containers():
            print("Failed to start Docker containers")  # noqa: T201
            return False

        if not self.wait_for_clickhouse():
            print("ClickHouse failed to start")  # noqa: T201
            return False

        if not self.wait_for_vertica():
            print("Vertica failed to start")  # noqa: T201
            return False

        print("\n=== Both databases are ready! ===")  # noqa: T201
        return True

    def _run_clickhouse_test(self, config, total_records, batch_size):
        """Запуск тестирования ClickHouse"""
        print("\n--- ClickHouse Testing ---")  # noqa: T201
        try:
            ch_test = ClickHouseTestSuite()
            ch_insert_time = ch_test.test_insert_performance(**config)
            ch_query_times = ch_test.test_query_performance()

            self.results["clickhouse"][
                f"records_{total_records}_batch_{batch_size}"
            ] = {
                "insert_time": ch_insert_time,
                "query_times": ch_query_times,
                "avg_query_time": sum(ch_query_times) / len(ch_query_times),
                "records_per_second": total_records / ch_insert_time,
            }
        except Exception as e:
            print(f"ClickHouse test failed: {e}")  # noqa: T201
            self.results["clickhouse"][
                f"records_{total_records}_batch_{batch_size}"
            ] = {"error": str(e)}

    def _run_vertica_test(self, config, total_records, batch_size):
        """Запуск тестирования Vertica"""
        print("\n--- Vertica Testing ---")  # noqa: T201
        try:
            vertica_test = VerticaTestSuite()
            vertica_insert_time = vertica_test.test_insert_performance(
                **config,
            )
            vertica_query_times = vertica_test.test_query_performance()

            self.results["vertica"][
                f"records_{total_records}_batch_{batch_size}"
            ] = {
                "insert_time": vertica_insert_time,
                "query_times": vertica_query_times,
                "avg_query_time": sum(vertica_query_times)
                / len(vertica_query_times),
                "records_per_second": total_records / vertica_insert_time,
            }

        except Exception as e:
            print(f"Vertica test failed: {e}")  # noqa: T201
            self.results["vertica"][
                f"records_{total_records}_batch_{batch_size}"
            ] = {"error": str(e)}

    def _calculate_comparison(self, total_records, batch_size):
        """Расчет сравнительных метрик"""
        ch_key = f"records_{total_records}_batch_{batch_size}"
        ch_data = self.results["clickhouse"].get(ch_key, {})
        vertica_data = self.results["vertica"].get(ch_key, {})

        if "error" not in ch_data and "error" not in vertica_data:
            insert_ratio = vertica_data["insert_time"] / ch_data["insert_time"]
            query_ratio = (
                vertica_data["avg_query_time"] / ch_data["avg_query_time"]
            )
            throughput_ratio = (
                ch_data["records_per_second"]
                / vertica_data["records_per_second"]
            )

            self.results["comparison"][ch_key] = {
                "insert_ratio_vertica_to_clickhouse": insert_ratio,
                "query_ratio_vertica_to_clickhouse": query_ratio,
                "throughput_ratio_clickhouse_to_vertica": throughput_ratio,
            }

            print(  # noqa: T201
                f"\n--- Comparison Results for {total_records:,} records, "
                f"batch {batch_size:,} ---",
            )

            print(  # noqa: T201
                f"Insert time ratio (Vertica/ClickHouse): {insert_ratio:.2f}x",
            )
            print(  # noqa: T201
                f"Query time ratio (Vertica/ClickHouse): {query_ratio:.2f}x",
            )
            print(  # noqa: T201
                f"Throughput ratio (ClickHouse/Vertica): {throughput_ratio:.2f}x",  # noqa: E501
            )
            ch_rps = ch_data["records_per_second"]
            vertica_rps = vertica_data["records_per_second"]
            print(  # noqa: T201
                f"ClickHouse throughput: {ch_rps:,.0f} records/sec",
            )
            print(  # noqa: T201
                f"Vertica throughput: {vertica_rps:,.0f} records/sec",
            )

    def run_comprehensive_test(self):
        """Запуск комплексного тестирования производительности"""
        test_configs = [
            {
                "total_records": 100_000,
                "batch_size": 1000,
                "num_processes": 4,
            },
            {
                "total_records": 100_000,
                "batch_size": 5000,
                "num_processes": 4,
            },
            {
                "total_records": 3_000_000,
                "batch_size": 10_000,
                "num_processes": 6,
            },
            {
                "total_records": 3_000_000,
                "batch_size": 25_000,
                "num_processes": 6,
            },
            {
                "total_records": 5_000_000,
                "batch_size": 50_000,
                "num_processes": 6,
            },
            {
                "total_records": 10_000_000,
                "batch_size": 100_000,
                "num_processes": 6,
            },
        ]

        for config in test_configs:
            batch_size = config["batch_size"]
            total_records = config["total_records"]
            print(f"\n{'=' * 80}")  # noqa: T201
            print(  # noqa: T201
                f"Testing: {total_records:,} records, "
                f"batch size: {batch_size:,}",
            )
            print(f"{'=' * 80}")  # noqa: T201

            self._run_clickhouse_test(config, total_records, batch_size)
            self._run_vertica_test(config, total_records, batch_size)
            self._calculate_comparison(total_records, batch_size)

            if total_records >= 1_000_000:
                print(  # noqa: T201
                    "\nWaiting 30 seconds for system stabilization...",
                )
                time.sleep(30)

        return True

    def generate_report(self):
        """Генерация отчета о результатах"""
        print("\n" + "=" * 80)  # noqa: T201
        print("DATABASE PERFORMANCE COMPARISON REPORT")  # noqa: T201
        print("=" * 80)  # noqa: T201

        for batch_key in self.results.get("clickhouse", {}).keys():
            batch_size = batch_key.split("_")[1]
            ch_data = self.results["clickhouse"].get(batch_key, {})
            vertica_data = self.results["vertica"].get(batch_key, {})
            comparison_data = self.results["comparison"].get(batch_key, {})

            print(f"\nBatch Size: {batch_size}")  # noqa: T201
            print("-" * 40)  # noqa: T201

            if "error" in ch_data:
                print(f"ClickHouse: ERROR - {ch_data['error']}")  # noqa: T201
            else:
                insert_time = ch_data.get("insert_time", "N/A")
                avg_query_time = ch_data.get("avg_query_time", "N/A")
                print(  # noqa: T201
                    f"ClickHouse Insert Time: {insert_time:.2f}s",
                )
                print(  # noqa: T201
                    f"ClickHouse Avg Query Time: {avg_query_time:.3f}s",
                )

            if "error" in vertica_data:
                print(  # noqa: T201
                    f"Vertica: ERROR - {vertica_data['error']}",
                )
            else:
                insert_time = vertica_data.get("insert_time", "N/A")
                avg_query_time = vertica_data.get("avg_query_time", "N/A")
                print(f"Vertica Insert Time: {insert_time:.2f}s")  # noqa: T201
                print(  # noqa: T201
                    f"Vertica Avg Query Time: {avg_query_time:.3f}s",
                )

            if comparison_data:
                print("\nComparison (Vertica/ClickHouse):")  # noqa: T201
                insert_ratio = comparison_data.get(
                    "insert_ratio_vertica_to_clickhouse",
                    "N/A",
                )
                query_ratio = comparison_data.get(
                    "query_ratio_vertica_to_clickhouse",
                    "N/A",
                )
                print(f"Insert Ratio: {insert_ratio:.2f}x")  # noqa: T201
                print(f"Query Ratio: {query_ratio:.2f}x")  # noqa: T201

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_comparison_results_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to {filename}")  # noqa: T201

    def run_full_comparison(self):
        """Запуск полного цикла сравнения"""
        try:
            if not self.setup_environment():
                print("Environment setup failed")  # noqa: T201
                return False

            if not self.run_comprehensive_test():
                print("Testing failed")  # noqa: T201
                return False

            self.generate_report()

            print(  # noqa: T201
                "\n=== Performance comparison completed successfully! ===",
            )
            return True

        except Exception as e:
            print(f"Error during performance comparison: {e}")  # noqa: T201
            return False


if __name__ == "__main__":
    comparison = PerformanceComparison()
    success = comparison.run_full_comparison()
    sys.exit(0 if success else 1)

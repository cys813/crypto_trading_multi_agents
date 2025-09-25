"""
Performance benchmarking script for the Enhanced Exchange Manager.

This script provides comprehensive performance testing including:
- Load testing with concurrent requests
- Latency measurements
- Throughput analysis
- Failover performance
- Resource utilization monitoring
"""

import asyncio
import time
import statistics
import psutil
import tracemalloc
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import json
import logging

# Import the enhanced exchange manager
import sys
sys.path.append('src')
from data_collection.core.enhanced_exchange_manager import ExchangeManager, ConnectionStrategy, Priority


@dataclass
class BenchmarkResult:
    """Benchmark result data class."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p95_latency: float
    p99_latency: float
    throughput_rps: float
    duration_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    errors: List[str] = field(default_factory=list)


class ExchangeManagerBenchmark:
    """Performance benchmark for Exchange Manager."""

    def __init__(self):
        self.logger = self._setup_logger()
        self.results: List[BenchmarkResult] = []
        self.exchange_manager = None

    def _setup_logger(self) -> logging.Logger:
        """Setup benchmark logger."""
        logger = logging.getLogger("benchmark")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def setup(self):
        """Setup benchmark environment."""
        self.logger.info("Setting up benchmark environment...")

        # Start memory tracing
        tracemalloc.start()

        # Initialize exchange manager
        self.exchange_manager = ExchangeManager(ConnectionStrategy.WEIGHTED_ROUND_ROBIN)

        # Mock exchanges for testing
        await self._setup_mock_exchanges()

        self.logger.info("Benchmark environment setup complete")

    async def _setup_mock_exchanges(self):
        """Setup mock exchanges for testing."""
        import ccxt
        from unittest.mock import AsyncMock

        # Create mock exchange classes
        mock_binance = AsyncMock()
        mock_binance.fetch_markets = AsyncMock(return_value=[
            {"symbol": "BTC/USDT", "active": True},
            {"symbol": "ETH/USDT", "active": True}
        ])
        mock_binance.fetch_ticker = AsyncMock(return_value={
            "symbol": "BTC/USDT", "last": 50000.0, "bid": 49900.0, "ask": 50100.0
        })
        mock_binance.fetch_ohlcv = AsyncMock(return_value=[
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]
        ])
        mock_binance.ping = AsyncMock()
        mock_binance.fetch_time = AsyncMock(return_value=time.time() * 1000)
        mock_binance.close = AsyncMock()
        mock_binance.timeout = 10000

        mock_okx = AsyncMock()
        mock_okx.fetch_markets = AsyncMock(return_value=[
            {"symbol": "BTC/USDT", "active": True},
            {"symbol": "ETH/USDT", "active": True}
        ])
        mock_okx.fetch_ticker = AsyncMock(return_value={
            "symbol": "BTC/USDT", "last": 50000.0, "bid": 49900.0, "ask": 50100.0
        })
        mock_okx.fetch_ohlcv = AsyncMock(return_value=[
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]
        ])
        mock_okx.ping = AsyncMock()
        mock_okx.fetch_time = AsyncMock(return_value=time.time() * 1000)
        mock_okx.close = AsyncMock()
        mock_okx.timeout = 10000

        # Patch ccxt module
        import sys
        sys.modules['ccxt.binance'] = lambda **kwargs: mock_binance
        sys.modules['ccxt.okx'] = lambda **kwargs: mock_okx

        # Initialize exchange manager
        await self.exchange_manager.initialize()

    async def run_load_test(self, concurrent_users: int, duration_seconds: int,
                          requests_per_user: int) -> BenchmarkResult:
        """Run load test with concurrent users."""
        test_name = f"Load Test - {concurrent_users} users, {duration_seconds}s"
        self.logger.info(f"Starting {test_name}")

        start_time = time.time()
        latencies = []
        errors = []

        async def make_requests(user_id: int):
            """Make requests for a single user."""
            user_latencies = []
            user_errors = []

            for i in range(requests_per_user):
                try:
                    request_start = time.time()
                    result = await self.exchange_manager.execute_request(
                        'fetch_ticker', 'BTC/USDT',
                        priority=Priority.NORMAL
                    )
                    latency = (time.time() - request_start) * 1000
                    user_latencies.append(latency)

                    # Small delay between requests
                    await asyncio.sleep(0.01)

                except Exception as e:
                    user_errors.append(str(e))

            return user_latencies, user_errors

        # Start memory monitoring
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        # Create concurrent users
        tasks = []
        for i in range(concurrent_users):
            task = make_requests(i)
            tasks.append(task)

        # Wait for all tasks to complete or timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=duration_seconds
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Load test timed out after {duration_seconds} seconds")
            results = []

        # Collect results
        all_latencies = []
        all_errors = []
        successful_requests = 0
        failed_requests = 0

        for result in results:
            if isinstance(result, Exception):
                all_errors.append(str(result))
                failed_requests += 1
            else:
                user_latencies, user_errors = result
                all_latencies.extend(user_latencies)
                all_errors.extend(user_errors)
                successful_requests += len(user_latencies)
                failed_requests += len(user_errors)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        # Calculate statistics
        if all_latencies:
            avg_latency = statistics.mean(all_latencies)
            min_latency = min(all_latencies)
            max_latency = max(all_latencies)
            p95_latency = np.percentile(all_latencies, 95)
            p99_latency = np.percentile(all_latencies, 99)
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = 0

        total_requests = successful_requests + failed_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        throughput_rps = successful_requests / duration_seconds

        benchmark_result = BenchmarkResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            avg_latency=avg_latency,
            min_latency=min_latency,
            max_latency=max_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            throughput_rps=throughput_rps,
            duration_seconds=time.time() - start_time,
            memory_usage_mb=final_memory - initial_memory,
            cpu_usage_percent=final_cpu - initial_cpu,
            errors=all_errors
        )

        self.results.append(benchmark_result)
        self.logger.info(f"Completed {test_name}")
        self._log_benchmark_result(benchmark_result)

        return benchmark_result

    async def run_latency_test(self, num_requests: int = 1000) -> BenchmarkResult:
        """Run latency test."""
        test_name = f"Latency Test - {num_requests} requests"
        self.logger.info(f"Starting {test_name}")

        start_time = time.time()
        latencies = []
        errors = []

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        for i in range(num_requests):
            try:
                request_start = time.time()
                result = await self.exchange_manager.execute_request(
                    'fetch_ticker', 'BTC/USDT',
                    priority=Priority.NORMAL
                )
                latency = (time.time() - request_start) * 1000
                latencies.append(latency)

            except Exception as e:
                errors.append(str(e))

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        successful_requests = len(latencies)
        failed_requests = len(errors)
        total_requests = successful_requests + failed_requests

        benchmark_result = BenchmarkResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=successful_requests / total_requests if total_requests > 0 else 0,
            avg_latency=statistics.mean(latencies) if latencies else 0,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p95_latency=np.percentile(latencies, 95) if latencies else 0,
            p99_latency=np.percentile(latencies, 99) if latencies else 0,
            throughput_rps=successful_requests / (time.time() - start_time),
            duration_seconds=time.time() - start_time,
            memory_usage_mb=final_memory - initial_memory,
            cpu_usage_percent=final_cpu - initial_cpu,
            errors=errors
        )

        self.results.append(benchmark_result)
        self.logger.info(f"Completed {test_name}")
        self._log_benchmark_result(benchmark_result)

        return benchmark_result

    async def test_load_balancing_strategies(self) -> List[BenchmarkResult]:
        """Test different load balancing strategies."""
        strategies = [
            ConnectionStrategy.ROUND_ROBIN,
            ConnectionStrategy.LEAST_LATENCY,
            ConnectionStrategy.WEIGHTED_ROUND_ROBIN,
            ConnectionStrategy.FAILOVER
        ]

        results = []

        for strategy in strategies:
            self.logger.info(f"Testing {strategy.value} strategy")

            # Set strategy
            self.exchange_manager.strategy = strategy

            # Run test
            start_time = time.time()
            latencies = []
            errors = []

            for i in range(100):  # 100 requests
                try:
                    request_start = time.time()
                    result = await self.exchange_manager.execute_request(
                        'fetch_ticker', 'BTC/USDT'
                    )
                    latency = (time.time() - request_start) * 1000
                    latencies.append(latency)
                except Exception as e:
                    errors.append(str(e))

            duration = time.time() - start_time
            successful_requests = len(latencies)
            failed_requests = len(errors)

            result = BenchmarkResult(
                test_name=f"Load Balancing - {strategy.value}",
                total_requests=successful_requests + failed_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=successful_requests / (successful_requests + failed_requests),
                avg_latency=statistics.mean(latencies) if latencies else 0,
                min_latency=min(latencies) if latencies else 0,
                max_latency=max(latencies) if latencies else 0,
                p95_latency=np.percentile(latencies, 95) if latencies else 0,
                p99_latency=np.percentile(latencies, 99) if latencies else 0,
                throughput_rps=successful_requests / duration,
                duration_seconds=duration,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                errors=errors
            )

            results.append(result)
            self.results.append(result)

        return results

    async def test_failover_performance(self) -> BenchmarkResult:
        """Test failover performance."""
        test_name = "Failover Performance Test"
        self.logger.info(f"Starting {test_name}")

        start_time = time.time()
        latencies = []
        errors = []

        # Simulate failover by marking one exchange as unhealthy
        if "binance" in self.exchange_manager.connections:
            self.exchange_manager.connections["binance"].status = ExchangeStatus.OFFLINE

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        # Make requests that should fail over to healthy exchange
        for i in range(50):
            try:
                request_start = time.time()
                result = await self.exchange_manager.execute_request(
                    'fetch_ticker', 'BTC/USDT'
                )
                latency = (time.time() - request_start) * 1000
                latencies.append(latency)
            except Exception as e:
                errors.append(str(e))

        # Restore exchange
        if "binance" in self.exchange_manager.connections:
            self.exchange_manager.connections["binance"].status = ExchangeStatus.HEALTHY

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        successful_requests = len(latencies)
        failed_requests = len(errors)
        total_requests = successful_requests + failed_requests

        benchmark_result = BenchmarkResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=successful_requests / total_requests if total_requests > 0 else 0,
            avg_latency=statistics.mean(latencies) if latencies else 0,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p95_latency=np.percentile(latencies, 95) if latencies else 0,
            p99_latency=np.percentile(latencies, 99) if latencies else 0,
            throughput_rps=successful_requests / (time.time() - start_time),
            duration_seconds=time.time() - start_time,
            memory_usage_mb=final_memory - initial_memory,
            cpu_usage_percent=final_cpu - initial_cpu,
            errors=errors
        )

        self.results.append(benchmark_result)
        self.logger.info(f"Completed {test_name}")
        self._log_benchmark_result(benchmark_result)

        return benchmark_result

    def _log_benchmark_result(self, result: BenchmarkResult):
        """Log benchmark result."""
        self.logger.info(f"""
{result.test_name} Results:
  Total Requests: {result.total_requests}
  Successful: {result.successful_requests} ({result.success_rate:.1%})
  Failed: {result.failed_requests}
  Avg Latency: {result.avg_latency:.2f}ms
  P95 Latency: {result.p95_latency:.2f}ms
  P99 Latency: {result.p99_latency:.2f}ms
  Throughput: {result.throughput_rps:.2f} RPS
  Duration: {result.duration_seconds:.2f}s
  Memory Usage: {result.memory_usage_mb:.2f}MB
  CPU Usage: {result.cpu_usage_percent:.1f}%
        """)

    def generate_report(self, output_file: str = "benchmark_report.json"):
        """Generate comprehensive benchmark report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_results": [self._result_to_dict(r) for r in self.results],
            "summary": self._generate_summary()
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Benchmark report saved to {output_file}")
        return report

    def _result_to_dict(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Convert benchmark result to dictionary."""
        return {
            "test_name": result.test_name,
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "failed_requests": result.failed_requests,
            "success_rate": result.success_rate,
            "avg_latency": result.avg_latency,
            "min_latency": result.min_latency,
            "max_latency": result.max_latency,
            "p95_latency": result.p95_latency,
            "p99_latency": result.p99_latency,
            "throughput_rps": result.throughput_rps,
            "duration_seconds": result.duration_seconds,
            "memory_usage_mb": result.memory_usage_mb,
            "cpu_usage_percent": result.cpu_usage_percent,
            "errors": result.errors[:10]  # Limit errors in report
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate benchmark summary."""
        if not self.results:
            return {}

        total_tests = len(self.results)
        avg_success_rate = statistics.mean([r.success_rate for r in self.results])
        avg_latency = statistics.mean([r.avg_latency for r in self.results])
        avg_throughput = statistics.mean([r.throughput_rps for r in self.results])
        total_memory = sum([r.memory_usage_mb for r in self.results])

        return {
            "total_tests": total_tests,
            "average_success_rate": avg_success_rate,
            "average_latency_ms": avg_latency,
            "average_throughput_rps": avg_throughput,
            "total_memory_usage_mb": total_memory,
            "best_performance": min(self.results, key=lambda x: x.avg_latency),
            "worst_performance": max(self.results, key=lambda x: x.avg_latency)
        }

    async def cleanup(self):
        """Cleanup benchmark environment."""
        self.logger.info("Cleaning up benchmark environment...")

        if self.exchange_manager:
            await self.exchange_manager.close()

        tracemalloc.stop()

        self.logger.info("Benchmark environment cleanup complete")


async def main():
    """Main benchmark execution function."""
    benchmark = ExchangeManagerBenchmark()

    try:
        # Setup
        await benchmark.setup()

        # Run tests
        print("Running Exchange Manager Performance Benchmarks...")
        print("=" * 60)

        # Latency test
        await benchmark.run_latency_test(1000)

        # Load tests
        await benchmark.run_load_test(10, 30, 10)  # 10 users, 30s, 10 req/user
        await benchmark.run_load_test(50, 30, 5)   # 50 users, 30s, 5 req/user
        await benchmark.run_load_test(100, 30, 3)  # 100 users, 30s, 3 req/user

        # Load balancing strategies
        await benchmark.test_load_balancing_strategies()

        # Failover test
        await benchmark.test_failover_performance()

        # Generate report
        report = benchmark.generate_report()

        print("\n" + "=" * 60)
        print("Benchmark Summary:")
        summary = report["summary"]
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Average Success Rate: {summary['average_success_rate']:.1%}")
        print(f"  Average Latency: {summary['average_latency_ms']:.2f}ms")
        print(f"  Average Throughput: {summary['average_throughput_rps']:.2f} RPS")
        print(f"  Total Memory Usage: {summary['total_memory_usage_mb']:.2f}MB")
        print("=" * 60)

    except Exception as e:
        benchmark.logger.error(f"Benchmark failed: {e}")
        raise
    finally:
        await benchmark.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
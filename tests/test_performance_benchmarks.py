"""
Performance benchmarks for Long Analyst Agent.

Provides standardized performance testing and benchmarking
with detailed metrics and comparisons.
"""

import asyncio
import time
import statistics
import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from tests.conftest import assert_performance_result, performance_thresholds

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmark framework."""

    def __init__(self, name: str):
        self.name = name
        self.results = []
        self.metadata = {}

    def run_benchmark(self, func, *args, **kwargs):
        """Run a single benchmark iteration."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)

        end_time = time.time()
        end_memory = self._get_memory_usage()

        benchmark_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time": end_time - start_time,
            "memory_usage": end_memory - start_memory,
            "success": success,
            "error": error,
            "result": result
        }

        self.results.append(benchmark_result)
        return benchmark_result

    def run_multiple_iterations(self, func, iterations: int, *args, **kwargs):
        """Run benchmark for multiple iterations."""
        logger.info(f"Running benchmark '{self.name}' for {iterations} iterations")

        for i in range(iterations):
            iteration_result = self.run_benchmark(func, *args, **kwargs)

            if i % 10 == 0:  # Log every 10 iterations
                logger.info(f"Iteration {i+1}/{iterations}: {iteration_result['execution_time']:.3f}s")

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Get benchmark summary statistics."""
        if not self.results:
            return {"error": "No results available"}

        successful_results = [r for r in self.results if r["success"]]
        failed_results = [r for r in self.results if not r["success"]]

        execution_times = [r["execution_time"] for r in successful_results]
        memory_usage = [r["memory_usage"] for r in successful_results if r["memory_usage"] is not None]

        summary = {
            "benchmark_name": self.name,
            "total_iterations": len(self.results),
            "successful_iterations": len(successful_results),
            "failed_iterations": len(failed_results),
            "success_rate": len(successful_results) / len(self.results) if self.results else 0,
            "execution_time_stats": {
                "min": min(execution_times) if execution_times else 0,
                "max": max(execution_times) if execution_times else 0,
                "mean": statistics.mean(execution_times) if execution_times else 0,
                "median": statistics.median(execution_times) if execution_times else 0,
                "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                "percentile_95": statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times) if execution_times else 0
            },
            "memory_usage_stats": {
                "min": min(memory_usage) if memory_usage else 0,
                "max": max(memory_usage) if memory_usage else 0,
                "mean": statistics.mean(memory_usage) if memory_usage else 0,
                "median": statistics.median(memory_usage) if memory_usage else 0
            },
            "failures": failed_results[:5] if failed_results else [],  # Show first 5 failures
            "metadata": self.metadata
        }

        return summary

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return None


class DataProcessingBenchmark(PerformanceBenchmark):
    """Benchmark for data processing performance."""

    def __init__(self):
        super().__init__("data_processing")
        self.metadata = {
            "description": "Benchmark for market data processing pipeline",
            "test_data_size": "1000 data points",
            "processing_stages": ["validation", "normalization", "enrichment"]
        }

    async def benchmark_data_processing(self, data_receiver, test_data_generator, iterations: int = 100):
        """Benchmark data processing performance."""
        def process_single_data_point():
            data = test_data_generator()
            return asyncio.run(data_receiver.process_market_data(data))

        return self.run_multiple_iterations(process_single_data_point, iterations)


class IndicatorCalculationBenchmark(PerformanceBenchmark):
    """Benchmark for technical indicator calculation."""

    def __init__(self):
        super().__init__("indicator_calculation")
        self.metadata = {
            "description": "Benchmark for technical indicator calculations",
            "indicators_tested": ["RSI", "MACD", "Bollinger Bands", "SMA", "EMA"],
            "data_points": 500
        }

    async def benchmark_indicator_calculation(self, indicators_engine, price_data, indicators_list, iterations: int = 50):
        """Benchmark indicator calculation performance."""
        def calculate_indicators():
            return asyncio.run(indicators_engine.calculate_indicators_batch(price_data, indicators_list))

        return self.run_multiple_iterations(calculate_indicators, iterations)


class SignalRecognitionBenchmark(PerformanceBenchmark):
    """Benchmark for signal recognition performance."""

    def __init__(self):
        super().__init__("signal_recognition")
        self.metadata = {
            "description": "Benchmark for signal recognition algorithms",
            "signal_types": ["trend", "momentum", "volatility", "pattern"],
            "market_conditions": "varied"
        }

    async def benchmark_signal_recognition(self, signal_recognizer, market_data_generator, iterations: int = 100):
        """Benchmark signal recognition performance."""
        def recognize_signals():
            data = market_data_generator()
            return asyncio.run(signal_recognizer.recognize_signals(data))

        return self.run_multiple_iterations(recognize_signals, iterations)


class LLMAnalysisBenchmark(PerformanceBenchmark):
    """Benchmark for LLM analysis performance."""

    def __init__(self):
        super().__init__("llm_analysis")
        self.metadata = {
            "description": "Benchmark for LLM-based market analysis",
            "analysis_types": ["sentiment", "trend", "risk"],
            "context_size": "medium"
        }

    async def benchmark_llm_analysis(self, llm_integration, context_generator, iterations: int = 20):
        """Benchmark LLM analysis performance."""
        def analyze_market():
            context = context_generator()
            return llm_integration.generate_analysis_prompt(context)

        return self.run_multiple_iterations(analyze_market, iterations)


class WinRateCalculationBenchmark(PerformanceBenchmark):
    """Benchmark for win rate calculation performance."""

    def __init__(self):
        super().__init__("winrate_calculation")
        self.metadata = {
            "description": "Benchmark for win rate calculation algorithms",
            "calculation_methods": ["simple", "weighted", "statistical"],
            "data_set_size": 1000
        }

    async def benchmark_winrate_calculation(self, winrate_calculator, signals_generator, iterations: int = 50):
        """Benchmark win rate calculation performance."""
        def calculate_winrate():
            signals = signals_generator()
            return asyncio.run(winrate_calculator.calculate_win_rate(signals))

        return self.run_multiple_iterations(calculate_winrate, iterations)


class ReportGenerationBenchmark(PerformanceBenchmark):
    """Benchmark for report generation performance."""

    def __init__(self):
        super().__init__("report_generation")
        self.metadata = {
            "description": "Benchmark for report generation",
            "report_formats": ["JSON", "HTML", "PDF", "Markdown"],
            "template_types": ["standard", "detailed", "executive"]
        }

    async def benchmark_report_generation(self, report_generator, data_generator, format_type, iterations: int = 30):
        """Benchmark report generation performance."""
        def generate_report():
            data = data_generator()
            return asyncio.run(report_generator.generate_report(data, format=format_type))

        return self.run_multiple_iterations(generate_report, iterations)


class MemoryUsageBenchmark(PerformanceBenchmark):
    """Benchmark for memory usage optimization."""

    def __init__(self):
        super().__init__("memory_usage")
        self.metadata = {
            "description": "Benchmark for memory usage and optimization",
            "test_duration": "60 seconds",
            "load_pattern": "increasing"
        }

    async def benchmark_memory_usage(self, component_factory, iterations: int = 10):
        """Benchmark memory usage under load."""
        import psutil
        import gc

        def memory_test_iteration():
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

            # Create components
            components = []
            for i in range(100):
                component = component_factory()
                components.append(component)

            # Process some data
            for component in components[:50]:  # Use subset
                if hasattr(component, 'process'):
                    component.process({"test": "data"})

            # Force cleanup
            components.clear()
            gc.collect()

            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            return final_memory - initial_memory

        return self.run_multiple_iterations(memory_test_iteration, iterations)


class ConcurrencyBenchmark(PerformanceBenchmark):
    """Benchmark for concurrent request handling."""

    def __init__(self):
        super().__init__("concurrency")
        self.metadata = {
            "description": "Benchmark for concurrent request handling",
            "concurrency_levels": [1, 10, 50, 100, 200],
            "request_types": ["data_processing", "analysis", "reporting"]
        }

    async def benchmark_concurrency(self, handler_func, concurrency_levels: List[int], iterations_per_level: int = 10):
        """Benchmark performance under different concurrency levels."""
        results = {}

        for concurrency in concurrency_levels:
            logger.info(f"Testing concurrency level: {concurrency}")

            async def run_concurrent_test():
                tasks = []
                for _ in range(concurrency):
                    task = asyncio.create_task(handler_func())
                    tasks.append(task)

                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                successful = sum(1 for r in results if not isinstance(r, Exception))
                return {
                    "concurrency": concurrency,
                    "execution_time": end_time - start_time,
                    "successful_requests": successful,
                    "failed_requests": concurrency - successful,
                    "throughput": concurrency / (end_time - start_time)
                }

            # Run multiple iterations for each concurrency level
            level_results = []
            for _ in range(iterations_per_level):
                result = await run_concurrent_test()
                level_results.append(result)

            # Calculate statistics for this concurrency level
            execution_times = [r["execution_time"] for r in level_results]
            throughputs = [r["throughput"] for r in level_results]

            results[f"concurrency_{concurrency}"] = {
                "avg_execution_time": statistics.mean(execution_times),
                "avg_throughput": statistics.mean(throughputs),
                "min_throughput": min(throughputs),
                "max_throughput": max(throughputs),
                "success_rate": sum(r["successful_requests"] for r in level_results) / (concurrency * iterations_per_level)
            }

        return results


@pytest.mark.performance
@pytest.mark.slow
async def test_data_processing_benchmark(test_config_manager, sample_market_data):
    """Test data processing performance benchmark."""
    from src.long_analyst.data_processing.data_receiver import DataReceiver

    data_receiver = DataReceiver(test_config_manager)

    def generate_test_data():
        import random
        return {
            "symbol": "BTC/USDT",
            "timestamp": datetime.utcnow().isoformat(),
            "open": 50000 + random.uniform(-1000, 1000),
            "high": 50500 + random.uniform(-1000, 1000),
            "low": 49500 + random.uniform(-1000, 1000),
            "close": 50200 + random.uniform(-1000, 1000),
            "volume": 1000 + random.randint(-500, 500)
        }

    benchmark = DataProcessingBenchmark()
    result = await benchmark.benchmark_data_processing(data_receiver, generate_test_data, iterations=100)

    # Verify performance meets thresholds
    avg_time = result["execution_time_stats"]["mean"]
    threshold = performance_thresholds()["max_data_processing_time"]

    assert avg_time <= threshold, f"Data processing time {avg_time:.3f}s exceeds threshold {threshold}s"

    return result


@pytest.mark.performance
@pytest.mark.slow
async def test_indicator_calculation_benchmark(test_config_manager, sample_price_series):
    """Test indicator calculation performance benchmark."""
    from src.long_analyst.indicators.indicators_engine import IndicatorsEngine

    indicators_engine = IndicatorsEngine(test_config_manager)
    indicators_list = ["rsi", "macd", "bollinger", "sma", "ema"]

    benchmark = IndicatorCalculationBenchmark()
    result = await benchmark.benchmark_indicator_calculation(
        indicators_engine, sample_price_series, indicators_list, iterations=50
    )

    # Verify performance meets thresholds
    avg_time = result["execution_time_stats"]["mean"]
    threshold = performance_thresholds()["max_indicator_calculation_time"]

    assert avg_time <= threshold, f"Indicator calculation time {avg_time:.3f}s exceeds threshold {threshold}s"

    return result


@pytest.mark.performance
@pytest.mark.slow
async def test_signal_recognition_benchmark(test_config_manager, sample_indicators):
    """Test signal recognition performance benchmark."""
    from src.long_analyst.signal_recognition.signal_recognizer import SignalRecognizer

    signal_recognizer = SignalRecognizer(test_config_manager)

    def generate_market_data():
        import random
        return {
            "symbol": "BTC/USDT",
            "price": 50000 + random.uniform(-2000, 2000),
            "indicators": {
                "rsi": random.uniform(20, 80),
                "macd": {
                    "macd": random.uniform(-200, 200),
                    "signal": random.uniform(-150, 150),
                    "histogram": random.uniform(-50, 50)
                },
                "bollinger": {
                    "upper": 52000 + random.uniform(-1000, 1000),
                    "middle": 50000 + random.uniform(-1000, 1000),
                    "lower": 48000 + random.uniform(-1000, 1000)
                }
            }
        }

    benchmark = SignalRecognitionBenchmark()
    result = await benchmark.benchmark_signal_recognition(signal_recognizer, generate_market_data, iterations=100)

    # Verify performance meets thresholds
    avg_time = result["execution_time_stats"]["mean"]
    threshold = performance_thresholds()["max_signal_recognition_time"]

    assert avg_time <= threshold, f"Signal recognition time {avg_time:.3f}s exceeds threshold {threshold}s"

    return result


@pytest.mark.performance
@pytest.mark.slow
async def test_llm_analysis_benchmark(test_config_manager, sample_signals):
    """Test LLM analysis performance benchmark."""
    from src.long_analyst.llm.llm_integration import LLMIntegration

    llm_integration = LLMIntegration(test_config_manager)

    def generate_context():
        import random
        return [
            {"role": "system", "content": "You are a trading analyst"},
            {"role": "user", "content": f"Analyze {random.choice(['BTC', 'ETH', 'BNB'])} market with confidence {random.uniform(0.6, 0.95)}"}
        ]

    benchmark = LLMAnalysisBenchmark()
    result = await benchmark.benchmark_llm_analysis(llm_integration, generate_context, iterations=20)

    # Verify performance meets thresholds
    avg_time = result["execution_time_stats"]["mean"]
    threshold = performance_thresholds()["max_llm_response_time"]

    assert avg_time <= threshold, f"LLM analysis time {avg_time:.3f}s exceeds threshold {threshold}s"

    return result


@pytest.mark.performance
@pytest.mark.slow
async def test_report_generation_benchmark(test_config_manager, sample_analysis_results):
    """Test report generation performance benchmark."""
    from src.long_analyst.reporting.report_generator import ReportGenerator

    report_generator = ReportGenerator(test_config_manager)

    def generate_report_data():
        import random
        return {
            "analysis_results": {
                "signals": [{"type": random.choice(["buy", "sell", "hold"]), "confidence": random.uniform(0.6, 0.95)}],
                "market_data": {"symbol": "BTC/USDT", "price": 50000 + random.uniform(-2000, 2000)}
            },
            "performance_metrics": {
                "win_rate": random.uniform(0.6, 0.9),
                "total_signals": random.randint(50, 200)
            }
        }

    formats_to_test = ["json", "html", "markdown"]
    format_results = {}

    for format_type in formats_to_test:
        benchmark = ReportGenerationBenchmark()
        result = await benchmark.benchmark_report_generation(
            report_generator, generate_report_data, format_type, iterations=30
        )

        # Verify performance meets thresholds
        avg_time = result["execution_time_stats"]["mean"]
        threshold = performance_thresholds()["max_report_generation_time"]

        assert avg_time <= threshold, f"Report generation time for {format_type} {avg_time:.3f}s exceeds threshold {threshold}s"

        format_results[format_type] = result

    return format_results


@pytest.mark.performance
@pytest.mark.slow
async def test_memory_usage_benchmark(test_config_manager):
    """Test memory usage benchmark."""
    from src.long_analyst.data_processing.data_receiver import DataReceiver

    def create_component():
        return DataReceiver(test_config_manager)

    benchmark = MemoryUsageBenchmark()
    result = await benchmark.benchmark_memory_usage(create_component, iterations=10)

    # Verify memory usage meets thresholds
    avg_memory_increase = result["execution_time_stats"]["mean"]
    threshold = performance_thresholds()["max_memory_usage_mb"]

    assert avg_memory_increase <= threshold, f"Memory increase {avg_memory_increase:.1f}MB exceeds threshold {threshold}MB"

    return result


@pytest.mark.performance
@pytest.mark.slow
async def test_concurrency_benchmark(test_config_manager):
    """Test concurrency performance benchmark."""
    from src.long_analyst.signal_recognition.signal_recognizer import SignalRecognizer

    signal_recognizer = SignalRecognizer(test_config_manager)

    async def handle_request():
        import random
        market_data = {
            "symbol": "BTC/USDT",
            "price": 50000 + random.uniform(-2000, 2000),
            "indicators": {
                "rsi": random.uniform(20, 80),
                "macd": {
                    "macd": random.uniform(-200, 200),
                    "signal": random.uniform(-150, 150)
                }
            }
        }
        signals = await signal_recognizer.recognize_signals(market_data)
        return signals

    benchmark = ConcurrencyBenchmark()
    concurrency_levels = [1, 10, 25, 50, 100]
    result = await benchmark.benchmark_concurrency(handle_request, concurrency_levels, iterations_per_level=5)

    # Verify performance doesn't degrade significantly with concurrency
    base_throughput = result["concurrency_1"]["avg_throughput"]
    high_concurrency_throughput = result["concurrency_50"]["avg_throughput"]

    # Should maintain at least 50% efficiency at 50x concurrency
    efficiency = high_concurrency_throughput / (base_throughput * 50)
    assert efficiency >= 0.5, f"Concurrency efficiency {efficiency:.2%} below 50% threshold"

    return result


@pytest.mark.performance
async def test_benchmark_comparison(test_config_manager):
    """Test performance comparison across different components."""
    from src.long_analyst.data_processing.data_receiver import DataReceiver
    from src.long_analyst.indicators.indicators_engine import IndicatorsEngine
    from src.long_analyst.signal_recognition.signal_recognizer import SignalRecognizer

    # Initialize components
    data_receiver = DataReceiver(test_config_manager)
    indicators_engine = IndicatorsEngine(test_config_manager)
    signal_recognizer = SignalRecognizer(test_config_manager)

    # Run benchmarks for each component
    benchmarks = {}

    # Data processing benchmark
    def data_processing_task():
        import random
        data = {
            "symbol": "BTC/USDT",
            "timestamp": datetime.utcnow().isoformat(),
            "open": 50000 + random.uniform(-1000, 1000),
            "high": 50500 + random.uniform(-1000, 1000),
            "low": 49500 + random.uniform(-1000, 1000),
            "close": 50200 + random.uniform(-1000, 1000),
            "volume": 1000 + random.randint(-500, 500)
        }
        return asyncio.run(data_receiver.process_market_data(data))

    benchmark = PerformanceBenchmark("data_processing_comparison")
    benchmarks["data_processing"] = benchmark.run_multiple_iterations(data_processing_task, 50)

    # Indicator calculation benchmark
    def indicator_calculation_task():
        price_data = [50000 + i * 100 for i in range(100)]
        return asyncio.run(indicators_engine.calculate_indicators_batch(price_data, ["rsi", "macd"]))

    benchmark = PerformanceBenchmark("indicator_calculation_comparison")
    benchmarks["indicator_calculation"] = benchmark.run_multiple_iterations(indicator_calculation_task, 30)

    # Signal recognition benchmark
    def signal_recognition_task():
        import random
        market_data = {
            "symbol": "BTC/USDT",
            "price": 50000 + random.uniform(-2000, 2000),
            "indicators": {
                "rsi": random.uniform(20, 80),
                "macd": {"macd": random.uniform(-200, 200), "signal": random.uniform(-150, 150)}
            }
        }
        return asyncio.run(signal_recognizer.recognize_signals(market_data))

    benchmark = PerformanceBenchmark("signal_recognition_comparison")
    benchmarks["signal_recognition"] = benchmark.run_multiple_iterations(signal_recognition_task, 40)

    # Generate comparison report
    comparison_report = {
        "benchmark_timestamp": datetime.utcnow().isoformat(),
        "components_tested": list(benchmarks.keys()),
        "performance_comparison": {},
        "relative_performance": {},
        "recommendations": []
    }

    # Compare performance
    baseline_time = benchmarks["data_processing"]["execution_time_stats"]["mean"]
    for component, result in benchmarks.items():
        avg_time = result["execution_time_stats"]["mean"]
        comparison_report["performance_comparison"][component] = {
            "avg_time_ms": avg_time * 1000,
            "relative_to_baseline": avg_time / baseline_time,
            "success_rate": result["success_rate"]
        }

        # Generate recommendations
        if avg_time > baseline_time * 2:
            comparison_report["recommendations"].append(
                f"Consider optimizing {component} - performance is {avg_time/baseline_time:.1f}x slower than baseline"
            )

    return comparison_report


@pytest.mark.performance
async def test_load_testing_benchmark(test_config_manager):
    """Test system performance under sustained load."""
    from src.long_analyst.data_processing.data_receiver import DataReceiver
    from src.long_analyst.indicators.indicators_engine import IndicatorsEngine

    data_receiver = DataReceiver(test_config_manager)
    indicators_engine = IndicatorsEngine(test_config_manager)

    # Simulate sustained load for 60 seconds
    load_duration = 60  # seconds
    requests_per_second = 10
    total_requests = load_duration * requests_per_second

    async def process_single_request():
        import random
        import time

        # Generate test data
        data = {
            "symbol": "BTC/USDT",
            "timestamp": datetime.utcnow().isoformat(),
            "open": 50000 + random.uniform(-1000, 1000),
            "high": 50500 + random.uniform(-1000, 1000),
            "low": 49500 + random.uniform(-1000, 1000),
            "close": 50200 + random.uniform(-1000, 1000),
            "volume": 1000 + random.randint(-500, 500)
        }

        start_time = time.time()

        # Process data
        processed = await data_receiver.process_market_data(data)

        # Calculate indicators
        indicators = await indicators_engine.calculate_indicators_batch(
            [processed["close"]], ["rsi", "macd"]
        )

        end_time = time.time()

        return {
            "success": True,
            "processing_time": end_time - start_time,
            "timestamp": datetime.utcnow()
        }

    # Run load test
    logger.info(f"Starting load test: {total_requests} requests over {load_duration} seconds")

    results = []
    start_time = time.time()

    for i in range(total_requests):
        result = await process_single_request()
        results.append(result)

        # Maintain request rate
        elapsed = time.time() - start_time
        expected_elapsed = i / requests_per_second
        if elapsed < expected_elapsed:
            await asyncio.sleep(expected_elapsed - elapsed)

    total_time = time.time() - start_time

    # Analyze results
    successful_requests = [r for r in results if r["success"]]
    processing_times = [r["processing_time"] for r in successful_requests]

    load_test_summary = {
        "test_duration_seconds": total_time,
        "total_requests": total_requests,
        "successful_requests": len(successful_requests),
        "success_rate": len(successful_requests) / total_requests,
        "requests_per_second": total_requests / total_time,
        "processing_time_stats": {
            "min": min(processing_times) if processing_times else 0,
            "max": max(processing_times) if processing_times else 0,
            "mean": statistics.mean(processing_times) if processing_times else 0,
            "median": statistics.median(processing_times) if processing_times else 0,
            "percentile_95": statistics.quantiles(processing_times, n=20)[18] if len(processing_times) >= 20 else max(processing_times) if processing_times else 0
        }
    }

    # Verify performance under load
    threshold = performance_thresholds()
    assert load_test_summary["success_rate"] >= threshold["min_success_rate"], \
        f"Load test success rate {load_test_summary['success_rate']:.2%} below threshold {threshold['min_success_rate']:.2%}"

    avg_processing_time = load_test_summary["processing_time_stats"]["mean"]
    assert avg_processing_time <= threshold["max_latency_ms"] / 1000, \
        f"Average processing time {avg_processing_time:.3f}s exceeds threshold {threshold['max_latency_ms']/1000}s"

    return load_test_summary
"""
Pytest configuration and fixtures for Long Analyst Agent tests.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import yaml
import json
from typing import Dict, Any

from src.long_analyst.config.config_manager import ConfigurationManager, ConfigEnvironment


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config_dir():
    """Create a temporary configuration directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="long_analyst_test_config_")

    # Create test configuration files
    config_files = {
        "technical_indicators.yaml": {
            "trend": {
                "sma": {"period": [20, 50, 200]},
                "ema": {"period": [12, 26]},
                "macd": {"fast": 12, "slow": 26, "signal": 9}
            },
            "momentum": {
                "rsi": {"period": 14},
                "stochastic": {"k_period": 14, "d_period": 3}
            },
            "volatility": {
                "bollinger_bands": {"period": 20, "std_dev": 2},
                "atr": {"period": 14}
            }
        },
        "signals.yaml": {
            "thresholds": {
                "min_confidence": 0.7,
                "max_signals": 10,
                "signal_timeout": 300
            },
            "risk_management": {
                "max_position_size": 0.1,
                "stop_loss": 0.02,
                "take_profit": 0.04
            }
        },
        "llm.yaml": {
            "providers": {
                "openai": {
                    "model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            },
            "cost_control": {
                "max_monthly_cost": 100,
                "cost_per_1k_tokens": 0.02
            }
        },
        "output.yaml": {
            "format": "json",
            "channels": ["api", "file", "email"],
            "templates": ["standard", "detailed"]
        }
    }

    # Write configuration files
    for filename, config_data in config_files.items():
        config_path = Path(temp_dir) / filename
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_config_manager(test_config_dir):
    """Create a test configuration manager."""
    config_manager = ConfigurationManager(
        config_dir=test_config_dir,
        environment=ConfigEnvironment.TESTING
    )

    yield config_manager

    # Shutdown
    asyncio.run(config_manager.shutdown())


@pytest.fixture(scope="function")
def sample_market_data():
    """Sample market data for testing."""
    return {
        "symbol": "BTC/USDT",
        "timestamp": "2025-09-27T10:00:00Z",
        "open": 50000.0,
        "high": 51000.0,
        "low": 49000.0,
        "close": 50500.0,
        "volume": 1000.0,
        "quote_volume": 50500000.0
    }


@pytest.fixture(scope="function")
def sample_price_series():
    """Sample price series for testing."""
    return [
        50000, 50200, 50500, 50300, 50800, 51200, 51000, 51500,
        51800, 52000, 51600, 51400, 51200, 51000, 50800, 50500,
        50300, 50000, 49800, 49500, 49300, 49500, 49800, 50200,
        50500, 50800, 51000, 51200, 51500, 51800, 52000, 52200
    ]


@pytest.fixture(scope="function")
def sample_indicators():
    """Sample indicators for testing."""
    return {
        "rsi": 65.5,
        "macd": {
            "macd": 125.3,
            "signal": 98.7,
            "histogram": 26.6
        },
        "bollinger": {
            "upper": 52500.0,
            "middle": 50500.0,
            "lower": 48500.0,
            "bandwidth": 0.04,
            "percent_b": 0.75
        },
        "sma": {
            "sma_20": 50500.0,
            "sma_50": 50200.0,
            "sma_200": 49500.0
        },
        "ema": {
            "ema_12": 50800.0,
            "ema_26": 50200.0
        }
    }


@pytest.fixture(scope="function")
def sample_signals():
    """Sample signals for testing."""
    return [
        {
            "type": "buy",
            "confidence": 0.85,
            "reason": "RSI oversold and price above SMA",
            "timestamp": "2025-09-27T10:00:00Z",
            "metadata": {
                "indicator_values": {"rsi": 32.5, "sma_20": 50000},
                "price_action": {"current": 50500, "change": 1.0}
            }
        },
        {
            "type": "hold",
            "confidence": 0.60,
            "reason": "Neutral trend with mixed signals",
            "timestamp": "2025-09-27T10:05:00Z",
            "metadata": {
                "indicator_values": {"rsi": 55.0, "macd": 0.0},
                "price_action": {"current": 50500, "change": 0.0}
            }
        }
    ]


@pytest.fixture(scope="function")
def sample_historical_signals():
    """Sample historical signals for win rate calculation."""
    return [
        {"signal": "buy", "outcome": "profit", "confidence": 0.8, "profit_loss": 500},
        {"signal": "buy", "outcome": "loss", "confidence": 0.6, "profit_loss": -300},
        {"signal": "sell", "outcome": "profit", "confidence": 0.7, "profit_loss": 400},
        {"signal": "buy", "outcome": "profit", "confidence": 0.9, "profit_loss": 800},
        {"signal": "hold", "outcome": "profit", "confidence": 0.5, "profit_loss": 100},
        {"signal": "sell", "outcome": "loss", "confidence": 0.6, "profit_loss": -200},
        {"signal": "buy", "outcome": "profit", "confidence": 0.8, "profit_loss": 600},
        {"signal": "sell", "outcome": "profit", "confidence": 0.7, "profit_loss": 300},
        {"signal": "hold", "outcome": "loss", "confidence": 0.4, "profit_loss": -100},
        {"signal": "buy", "outcome": "profit", "confidence": 0.85, "profit_loss": 700}
    ]


@pytest.fixture(scope="function")
def sample_analysis_results():
    """Sample analysis results for testing."""
    return {
        "market_data": {
            "symbol": "BTC/USDT",
            "current_price": 50500.0,
            "price_change_24h": 1.0,
            "volume_24h": 1000000.0
        },
        "indicators": {
            "trend": "bullish",
            "momentum": "strong",
            "volatility": "medium"
        },
        "signals": [
            {
                "type": "buy",
                "confidence": 0.85,
                "entry_price": 50500.0,
                "target_price": 52500.0,
                "stop_loss": 49000.0
            }
        ],
        "risk_analysis": {
            "risk_level": "medium",
            "position_size": 0.05,
            "potential_profit": 2000.0,
            "potential_loss": 1500.0,
            "risk_reward_ratio": 1.33
        },
        "llm_analysis": {
            "market_sentiment": "bullish",
            "confidence": 0.85,
            "key_factors": [
                "Increasing trading volume",
                "Positive technical indicators",
                "Strong market momentum"
            ]
        }
    }


@pytest.fixture(scope="session")
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "max_data_processing_time": 0.01,  # 10ms
        "max_indicator_calculation_time": 0.1,  # 100ms
        "max_signal_recognition_time": 0.05,  # 50ms
        "max_llm_response_time": 2.0,  # 2 seconds
        "max_report_generation_time": 0.5,  # 500ms
        "min_success_rate": 0.95,  # 95%
        "max_memory_usage_mb": 100,
        "min_throughput_per_second": 100,
        "max_latency_ms": 100
    }


# Custom markers for pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests"
    )
    config.addinivalue_line(
        "markers", "optimization: marks tests as optimization tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


# Test utilities
def create_test_config_file(config_dir: str, filename: str, config_data: Dict[str, Any]) -> str:
    """Create a test configuration file."""
    config_path = Path(config_dir) / filename
    with open(config_path, 'w') as f:
        if filename.endswith('.json'):
            json.dump(config_data, f, indent=2)
        else:
            yaml.dump(config_data, f, default_flow_style=False)
    return str(config_path)


def assert_performance_result(result: Dict[str, Any], threshold_name: str, thresholds: Dict[str, float]):
    """Assert that performance result meets threshold."""
    threshold = thresholds.get(threshold_name)
    if threshold is None:
        pytest.fail(f"Unknown threshold: {threshold_name}")

    passed = result.get("passed", False)
    if not passed:
        error_msg = result.get("error", "Performance test failed")
        pytest.fail(f"Performance test failed: {error_msg}")

    # Check specific performance metrics
    if "avg_time" in result:
        assert result["avg_time"] <= threshold, f"Average time {result['avg_time']} exceeds threshold {threshold}"

    if "throughput" in result:
        assert result["throughput"] >= threshold, f"Throughput {result['throughput']} below threshold {threshold}"

    if "success_rate" in result:
        assert result["success_rate"] >= threshold, f"Success rate {result['success_rate']} below threshold {threshold}"
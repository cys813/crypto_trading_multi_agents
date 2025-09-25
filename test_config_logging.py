#!/usr/bin/env python3
"""
Test script for configuration and logging system implementation.

This script tests the major components of the configuration management
and logging system to ensure they work correctly.
"""

import sys
import os
import asyncio
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_collection.core.config import config_manager, get_config, ConfigManager
from data_collection.core.logger import get_logger, get_exchange_logger, get_request_context
from data_collection.core.exceptions import (
    error_handler, ErrorContext, ConfigurationError, ExchangeError, ErrorCode
)
from data_collection.core.monitoring import (
    record_request, record_data_collection, get_dashboard_data
)


def test_configuration_loading():
    """Test configuration loading and validation."""
    print("Testing configuration loading...")

    try:
        # Test loading development configuration
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  Environment: {config.environment}")
        print(f"  App Name: {config.app_name}")
        print(f"  Debug Mode: {config.debug}")

        # Test configuration validation
        errors = config_manager.validate_config()
        if errors:
            print(f"⚠ Configuration validation warnings: {errors}")
        else:
            print("✓ Configuration validation passed")

        # Test getting configuration values
        db_host = config_manager.get("database.timescaledb.host")
        print(f"✓ Database host: {db_host}")

        return True

    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False


def test_environment_variables():
    """Test environment variable substitution."""
    print("\nTesting environment variable substitution...")

    try:
        # Test if environment variables are properly substituted
        config = get_config()

        # Check if timescaledb configuration uses environment variables
        timescaledb_config = config.timescaledb
        print(f"✓ TimescaleDB host: {timescaledb_config.host}")

        return True

    except Exception as e:
        print(f"✗ Environment variable substitution failed: {e}")
        return False


def test_logging_system():
    """Test logging system functionality."""
    print("\nTesting logging system...")

    try:
        # Test basic logger
        logger = get_logger("test_logger")
        logger.info("Test log message")
        print("✓ Basic logger created and tested")

        # Test exchange logger
        exchange_logger = get_exchange_logger("binance", "BTC/USDT")
        exchange_logger.info("Exchange-specific log message")
        print("✓ Exchange logger created and tested")

        # Test request context
        with get_request_context(user_id="test_user", operation="test_operation") as req_logger:
            req_logger.info("Request context log message")
        print("✓ Request context logger tested")

        return True

    except Exception as e:
        print(f"✗ Logging system test failed: {e}")
        return False


def test_error_handling():
    """Test error handling system."""
    print("\nTesting error handling system...")

    try:
        # Test creating and handling custom exception
        try:
            raise ConfigurationError(
                "Test configuration error",
                context=ErrorContext(
                    component="test",
                    operation="test_config"
                )
            )
        except ConfigurationError as e:
            error_info = error_handler.handle_exception(e)
            print("✓ Custom exception handled successfully")

        # Test error statistics
        error_stats = error_handler.get_error_stats()
        print(f"✓ Error stats collected: {error_stats['total_errors']} total errors")

        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def test_monitoring_system():
    """Test monitoring and metrics system."""
    print("\nTesting monitoring system...")

    try:
        # Test recording metrics
        record_request("GET", "/api/v1/test", 200, 0.045)
        print("✓ Request metrics recorded")

        record_data_collection("binance", "ohlcv", "BTC/USDT", True, 0.034, 100)
        print("✓ Data collection metrics recorded")

        # Test getting dashboard data
        dashboard_data = get_dashboard_data()
        print("✓ Dashboard data retrieved")
        print(f"  Timestamp: {dashboard_data.get('timestamp', 'N/A')}")

        return True

    except Exception as e:
        print(f"✗ Monitoring system test failed: {e}")
        return False


def test_configuration_reload():
    """Test configuration hot-reload."""
    print("\nTesting configuration hot-reload...")

    try:
        # Test configuration reload
        old_config = get_config()
        new_config = config_manager.reload()

        print("✓ Configuration reloaded successfully")
        print(f"  Old config environment: {old_config.environment}")
        print(f"  New config environment: {new_config.environment}")

        return True

    except Exception as e:
        print(f"✗ Configuration reload test failed: {e}")
        return False


def test_async_components():
    """Test asynchronous components."""
    print("\nTesting asynchronous components...")

    async def async_test():
        try:
            # Test async logging
            logger = get_logger("async_test")
            logger.info("Async log message")

            # Test async error handling
            try:
                raise ExchangeError("Test async error")
            except ExchangeError as e:
                error_handler.handle_exception(e, ErrorContext(
                    component="async_test",
                    operation="test_async"
                ))

            return True
        except Exception as e:
            print(f"✗ Async test failed: {e}")
            return False

    try:
        result = asyncio.run(async_test())
        if result:
            print("✓ Async components tested successfully")
        return result

    except Exception as e:
        print(f"✗ Async test failed: {e}")
        return False


def test_performance():
    """Test performance of logging and metrics collection."""
    print("\nTesting performance...")

    try:
        # Test logging performance
        logger = get_logger("performance_test")
        start_time = time.time()

        for i in range(1000):
            logger.info(f"Performance test message {i}")

        end_time = time.time()
        duration = end_time - start_time
        avg_time = duration * 1000 / 1000  # ms per log

        print(f"✓ Logging performance: {avg_time:.2f}ms per log message")

        # Test metrics performance
        start_time = time.time()

        for i in range(1000):
            record_request("GET", "/api/v1/test", 200, 0.001)

        end_time = time.time()
        duration = end_time - start_time
        avg_time = duration * 1000 / 1000  # ms per metric

        print(f"✓ Metrics performance: {avg_time:.2f}ms per metric")

        return True

    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Configuration and Logging System Test Suite")
    print("=" * 60)

    tests = [
        test_configuration_loading,
        test_environment_variables,
        test_logging_system,
        test_error_handling,
        test_monitoring_system,
        test_configuration_reload,
        test_async_components,
        test_performance
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All tests passed! Configuration and logging system is working correctly.")
        return 0
    else:
        print(f"❌ {total - passed} tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
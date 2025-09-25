# Configuration Management and Logging System

## Overview

The data collection agent features a comprehensive configuration management and logging system designed for reliability, security, and observability in production environments.

## Configuration Management

### Features

- **Multi-environment Support**: Separate configurations for development, testing, and production
- **Environment Variable Substitution**: Support for `${VARIABLE}` and `$VARIABLE` syntax
- **Configuration Validation**: Pydantic-based validation with type safety
- **Hot-reload Capability**: Automatically reload configuration when files change
- **Sensitive Data Encryption**: Encrypt API keys and passwords in configuration files
- **Hierarchical Configuration**: Structured configuration with nested sections

### Configuration Files

Configuration files are located in the `configs/` directory:

- `configs/development.yaml` - Development environment configuration
- `configs/testing.yaml` - Testing environment configuration
- `configs/production.yaml` - Production environment configuration

### Configuration Structure

```yaml
# Application settings
app:
  name: "data_collection_agent"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 8000
  environment: "production"

# Database configurations
database:
  timescaledb:
    host: "${TIMESCALEDB_HOST}"
    port: ${TIMESCALEDB_PORT}
    database: "${TIMESCALEDB_DATABASE}"
    username: "${TIMESCALEDB_USER}"
    password: "${TIMESCALEDB_PASSWORD}"
    pool_size: 50
    max_overflow: 20

  postgresql:
    host: "${POSTGRES_HOST}"
    port: ${POSTGRES_PORT}
    database: "${POSTGRES_DATABASE}"
    username: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
    pool_size: 30
    max_overflow: 10

  redis:
    host: "${REDIS_HOST}"
    port: ${REDIS_PORT}
    database: ${REDIS_DB}
    username: "${REDIS_USER}"
    password: "${REDIS_PASSWORD}"
    pool_size: 100
    max_overflow: 50

# Exchange configurations
exchanges:
  binance:
    enabled: true
    sandbox: false
    api_key: "${BINANCE_API_KEY}"
    api_secret: "${BINANCE_API_SECRET}"
    rate_limit: 100
    timeout: 15000
    enable_rate_limit: true

  okx:
    enabled: true
    sandbox: false
    api_key: "${OKX_API_KEY}"
    api_secret: "${OKX_API_SECRET}"
    passphrase: "${OKX_PASSPHRASE}"
    rate_limit: 20
    timeout: 15000
    enable_rate_limit: true

# Monitoring configuration
monitoring:
  prometheus_enabled: true
  prometheus_port: 9090
  prometheus_path: "/metrics"
  grafana_enabled: true
  grafana_host: "${GRAFANA_HOST}"
  grafana_port: ${GRAFANA_PORT}

# Logging configuration
logging:
  level: "INFO"
  format: "json"
  output: ["file", "remote"]
  file_path: "/var/log/data_collection/production.log"
  max_file_size: "500MB"
  backup_count: 30
  structured_logging: true

# Data collection configuration
collector:
  market_data_enabled: true
  positions_enabled: true
  orders_enabled: true
  symbols: ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
  timeframes: ["1m", "5m", "15m", "1h", "4h", "1d"]
  sync_interval: 1
  order_book_depth: 50
  trade_limit: 5000
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application Configuration
CONFIG_PATH=configs/development.yaml
ENCRYPTION_KEY=your-32-character-encryption-key-here
CONFIG_WATCH=true

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DATABASE=crypto_postgres

TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=password
TIMESCALEDB_DATABASE=timescaledb_crypto

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_USER=

# Exchange Configuration
BINANCE_TEST_API_KEY=your-binance-test-api-key
BINANCE_TEST_API_SECRET=your-binance-test-api-secret

OKX_TEST_API_KEY=your-okx-test-api-key
OKX_TEST_API_SECRET=your-okx-test-api-secret
OKX_TEST_PASSPHRASE=your-okx-test-passphrase
```

### Configuration Management API

#### Reload Configuration

```bash
curl -X POST "http://localhost:8000/api/v1/system/reload-config"
```

#### Validate Configuration

```bash
curl "http://localhost:8000/api/v1/system/config-validation"
```

#### Get System Information

```bash
curl "http://localhost:8000/api/v1/system/info"
```

### Configuration Encryption

To encrypt sensitive data in configuration files:

1. Set the `ENCRYPTION_KEY` environment variable (32-character string)
2. Use the configuration manager to encrypt values:

```python
from src.data_collection.core.config import config_manager

# Encrypt a value
encrypted_value = config_manager.encrypt_value("my_secret_password")

# Save encrypted configuration
config_manager.save_config("configs/production_encrypted.yaml")
```

### Configuration Validation

The system automatically validates configuration on startup and reload:

- Database connection parameters
- Exchange API credentials
- Port number ranges
- Log level validity
- File path accessibility

## Logging System

### Features

- **Structured Logging**: JSON format with consistent fields
- **Multiple Output Channels**: Console, file, and remote logging
- **Log Rotation**: Automatic file rotation based on size and count
- **Context-aware Logging**: Request ID and correlation ID support
- **Performance Monitoring**: Execution time tracking
- **Async Logging**: Non-blocking log writes for better performance

### Log Format

#### JSON Format (Production)

```json
{
  "timestamp": "2024-01-01T00:00:00.000Z",
  "level": "INFO",
  "logger": "exchange.binance.BTC_USDT",
  "message": "Successfully collected market data",
  "service": "data_collection_agent",
  "module": "market_data_collector",
  "function": "collect_ohlcv",
  "line": 123,
  "thread_id": 140123456789,
  "process_id": 12345,
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "request_id": "req_123456789",
  "duration_ms": 45.2
}
```

#### Text Format (Development)

```
2024-01-01 00:00:00 - exchange.binance.BTC_USDT - INFO - Successfully collected market data
```

### Logging Configuration

```yaml
logging:
  level: "INFO"                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"                   # json, text
  output: ["console", "file"]      # console, file, remote
  file_path: "logs/app.log"         # Log file path
  max_file_size: "100MB"           # Maximum file size
  backup_count: 10                  # Number of backup files
  structured_logging: true          # Enable structured logging
```

### Logger Usage

#### Basic Logging

```python
from src.data_collection.core.logger import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Failed to connect to database", extra={"component": "database"})
```

#### Context-aware Logging

```python
from src.data_collection.core.logger import get_exchange_logger, get_request_context

# Exchange-specific logger
exchange_logger = get_exchange_logger("binance", "BTC/USDT")
exchange_logger.info("Collected OHLCV data")

# Request context
with get_request_context(user_id="user123", operation="get_market_data") as logger:
    logger.info("Processing market data request")
```

#### Performance Logging

```python
from src.data_collection.core.logger import log_execution_time

logger = get_logger(__name__)

with log_execution_time(logger, "data_collection"):
    # Your code here
    data = collect_market_data()
```

#### Function Logging

```python
from src.data_collection.core.logger import log_function_call

@log_function_call
def collect_market_data(exchange, symbol):
    # Function implementation
    return data
```

## Error Handling

### Features

- **Custom Exception Types**: Specific exceptions for different error scenarios
- **Error Code System**: Standardized error codes for better tracking
- **Error Recovery**: Automatic retry mechanisms for recoverable errors
- **Error Statistics**: Comprehensive error tracking and analysis
- **Error Alerting**: Configurable alert thresholds and notifications

### Exception Types

```python
# Configuration errors
ConfigurationError, ConfigurationMissingError, ConfigurationValidationError

# Database errors
DatabaseError, DatabaseConnectionError, DatabaseTimeoutError

# Exchange errors
ExchangeError, ExchangeConnectionError, ExchangeRateLimitError

# Network errors
NetworkError, NetworkTimeoutError

# Data errors
DataError, DataValidationError, DataQualityError

# System errors
SystemError, MemoryError, DiskError

# Business errors
BusinessError, ValidationError

# Security errors
SecurityError
```

### Error Handling Patterns

#### Basic Error Handling

```python
from src.data_collection.core.exceptions import (
    ExchangeError, error_handler, ErrorContext, handle_exceptions
)

@handle_exceptions(ErrorContext(component="data_collector", operation="collect_data"))
def collect_data():
    try:
        # Your code here
        pass
    except ExchangeError as e:
        logger.error(f"Exchange error: {e}")
        raise
```

#### Retry Mechanisms

```python
from src.data_collection.core.exceptions import retry_on_error

@retry_on_error(
    max_retries=3,
    backoff_factor=1.0,
    retryable_errors=[ErrorCode.EXCHANGE_RATE_LIMIT, ErrorCode.NETWORK_TIMEOUT]
)
def api_call():
    # Your API call here
    pass
```

#### Error Context

```python
from src.data_collection.core.exceptions import error_context

with error_context(component="exchange_api", operation="get_ticker", exchange="binance"):
    # Your code here
    pass
```

### Error Statistics API

Access error statistics through the monitoring dashboard:

```bash
curl "http://localhost:8000/api/v1/system/metrics"
```

## Monitoring and Metrics

### Features

- **Prometheus Integration**: Native Prometheus metrics export
- **System Metrics**: CPU, memory, disk, network monitoring
- **Business Metrics**: Data collection, quality, and performance metrics
- **Custom Metrics**: User-defined metrics for specific use cases
- **Dashboard Integration**: Comprehensive dashboard data API

### Metrics Categories

#### System Metrics

- CPU usage percentage
- Memory usage (total, available, used)
- Disk usage and I/O
- Network I/O statistics
- Process-specific metrics

#### Application Metrics

- Request count and duration
- Error count by type
- Active connections
- Cache performance

#### Business Metrics

- Data collection operations
- Data quality scores
- API rate limit usage
- Exchange-specific statistics

### Metrics Access

#### Prometheus Endpoint

```bash
curl "http://localhost:8000/metrics"
```

#### Dashboard API

```bash
curl "http://localhost:8000/api/v1/system/metrics"
```

### Custom Metrics

```python
from src.data_collection.core.monitoring import metrics, MetricDefinition

# Add custom metric
metrics.add_custom_metric(MetricDefinition(
    name="custom_business_metric",
    type="counter",
    description="Custom business metric",
    labels=["service", "operation"]
))

# Use custom metric
custom_metric = metrics.get_custom_metric("custom_business_metric")
custom_metric.labels(service="data_collection", operation="process").inc()
```

## Best Practices

### Configuration

1. **Environment Separation**: Use different configuration files for each environment
2. **Secrets Management**: Never commit API keys or passwords to version control
3. **Configuration Validation**: Always validate configuration before deployment
4. **Encryption**: Encrypt sensitive data in configuration files
5. **Environment Variables**: Use environment variables for deployment-specific values

### Logging

1. **Structured Logging**: Use JSON format in production for better analysis
2. **Context Information**: Include relevant context in log messages
3. **Log Levels**: Use appropriate log levels for different message types
4. **Performance**: Use async logging to avoid blocking application threads
5. **Log Rotation**: Configure appropriate log rotation to prevent disk space issues

### Error Handling

1. **Specific Exceptions**: Use specific exception types for better error handling
2. **Error Context**: Always provide context information when handling errors
3. **Recovery Strategies**: Implement retry mechanisms for transient errors
4. **Error Monitoring**: Monitor error rates and set up appropriate alerts
5. **Documentation**: Document error codes and recovery procedures

### Monitoring

1. **Comprehensive Metrics**: Monitor system, application, and business metrics
2. **Alert Thresholds**: Set appropriate alert thresholds for different metrics
3. **Dashboard Access**: Provide easy access to monitoring dashboards
4. **Custom Metrics**: Add custom metrics for business-specific monitoring
5. **Performance Impact**: Minimize monitoring overhead on application performance

## Troubleshooting

### Common Issues

#### Configuration Loading Fails

1. Check configuration file syntax (YAML/JSON)
2. Verify environment variables are set correctly
3. Ensure configuration file paths are accessible
4. Validate encryption key for encrypted configurations

#### Logging Issues

1. Check file permissions for log directories
2. Verify disk space for log files
3. Ensure log format configuration is correct
4. Check async log queue capacity

#### Error Handling Issues

1. Verify error context information is complete
2. Check retry mechanism configuration
3. Monitor error rates and patterns
4. Validate alert threshold settings

#### Monitoring Issues

1. Verify Prometheus server accessibility
2. Check metric collection intervals
3. Monitor system resource usage by metrics collection
4. Validate custom metric definitions

### Debug Mode

Enable debug mode for detailed troubleshooting:

```yaml
app:
  debug: true

logging:
  level: "DEBUG"
  format: "text"
  output: ["console"]
```

## API Reference

### Configuration Manager

```python
from src.data_collection.core.config import config_manager, get_config

# Get configuration
config = get_config()

# Get configuration value
db_host = config_manager.get("database.timescaledb.host")

# Reload configuration
new_config = config_manager.reload()

# Validate configuration
errors = config_manager.validate_config()
```

### Logger Manager

```python
from src.data_collection.core.logger import (
    get_logger, get_exchange_logger, get_request_context
)

# Get logger
logger = get_logger("my_module")

# Get exchange logger
exchange_logger = get_exchange_logger("binance", "BTC/USDT")

# Request context
with get_request_context(user_id="user123") as logger:
    logger.info("Processing request")
```

### Error Handler

```python
from src.data_collection.core.exceptions import (
    error_handler, ErrorContext, handle_exceptions
)

# Handle exception
error_handler.handle_exception(exception, context)

# Error context
context = ErrorContext(
    component="my_component",
    operation="my_operation",
    exchange="binance",
    symbol="BTC/USDT"
)
```

### Monitoring

```python
from src.data_collection.core.monitoring import (
    record_request, record_data_collection, get_dashboard_data
)

# Record metrics
record_request("GET", "/api/v1/market", 200, 0.045)
record_data_collection("binance", "ohlcv", "BTC/USDT", True, 0.045, 1000)

# Get dashboard data
dashboard_data = get_dashboard_data()
```
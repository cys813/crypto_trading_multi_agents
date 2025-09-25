# Data Collection Agent Documentation

## Overview

The Data Collection Agent is a comprehensive, high-performance system for collecting real-time market data from multiple cryptocurrency exchanges. It supports OHLCV, ticker, order book, and trades data collection with intelligent scheduling, incremental updates, quality monitoring, and performance optimization.

## Architecture

### Core Components

1. **DataCollector** - Main orchestration engine
2. **Specialized Collectors** - Optimized collectors for different data types
3. **Storage Layer** - TimescaleDB + Redis for persistence and caching
4. **Quality Monitoring** - Real-time data validation and quality control
5. **Performance Optimization** - Caching, load balancing, and rate limiting

### Component Relationships

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DataCollector │    │ Exchange Manager │    │  Data Processor │
│   (Main Engine) │◄──►│   (API Layer)   │◄──►│ (Data Cleaning) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐              │
         │              │ Quality Monitor  │              │
         └─────────────►│ (Validation)     │◄─────────────┘
                        └──────────────────┘
                                │
         ┌─────────────────┐    │    ┌─────────────────┐
         │OrderBook Collector│    │    │ Trades Collector│
         │ (Real-time L2)  │    │    │ (Trade History) │
         └─────────────────┘    │    └─────────────────┘
                                │
         ┌─────────────────┐    │    ┌─────────────────┐
         │ Redis Storage   │    │    │TimescaleDB      │
         │ (Caching)       │◄───┼──►│ (Persistence)    │
         └─────────────────┘    │    └─────────────────┘
                                │
                        ┌───────┴───────┐
                        │ Load Balancer │
                        │ & Performance │
                        └───────────────┘
```

## Features

### 1. Intelligent Scheduling

- **Priority-based task scheduling** with dynamic prioritization
- **Load balancing** across multiple exchanges
- **Adaptive intervals** based on data freshness and system load
- **Resource optimization** with connection pooling and rate limiting

### 2. Incremental Data Fetching

- **Timestamp-based synchronization** for OHLCV data
- **Trade ID-based incremental updates** for trades data
- **Smart caching** of last collection points
- **Efficient bandwidth usage** with minimal redundant requests

### 3. Real-time Quality Monitoring

- **Multi-dimensional validation** (accuracy, completeness, timeliness)
- **Configurable quality thresholds** with automatic alerts
- **Anomaly detection** for unusual data patterns
- **Statistical analysis** of data quality trends

### 4. Performance Optimization

- **Multi-level caching** (Redis + in-memory)
- **Circuit breaker pattern** for fault tolerance
- **Rate limiting** to prevent API abuse
- **Connection pooling** for efficient resource usage
- **Batch processing** for bulk operations

### 5. Comprehensive Data Support

#### OHLCV Data
- Multiple timeframes (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- Incremental candle updates
- Volume and trade count validation
- Price consistency checks

#### Order Book Data
- Real-time L2 order book collection
- Configurable depth levels
- Spread and liquidity analysis
- Bid-ask imbalance detection

#### Trades Data
- Incremental trade history updates
- Trade side and type validation
- Large trade detection
- Volume-weighted average price calculation

#### Ticker Data
- Real-time price updates
- 24-hour statistics
- Price change tracking
- Market depth indicators

## Configuration

### Environment Variables

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=crypto_trading

TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=password
TIMESCALEDB_DB=timescaledb_crypto

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Data Collection Settings
DATA_COLLECTION_INTERVAL=1000
OHLCV_TIMEFRAMES=["1m","5m","15m","30m","1h","4h","1d"]
ORDER_BOOK_DEPTH=20
TRADE_LIMIT=1000

# Quality Control
DATA_QUALITY_THRESHOLD=0.999
MAX_RETRIES=3
RETRY_DELAY=1000

# Performance Settings
MAX_CONCURRENT_CONNECTIONS=1000
REQUEST_TIMEOUT=100
CACHE_TTL=300
```

### Configuration Example

```python
from src.data_collection.core.data_collector import DataCollector

# Initialize data collector
collector = DataCollector()

# Start collection system
await collector.start()

# Add custom collection tasks
await collector.add_collection_task(
    task_id="custom_btc_1m",
    exchange="binance",
    symbol="BTC/USDT",
    data_type="ohlcv",
    interval=60,
    parameters={"timeframe": "1m", "limit": 1000}
)

# Get collection status
status = collector.get_collection_status()
print(f"Active tasks: {status['active_tasks']}")
print(f"Success rate: {status['statistics']['success_rate']:.2%}")
```

## API Reference

### DataCollector Class

#### Methods

##### `async start()`
Start the data collection system.

##### `async stop()`
Stop the data collection system gracefully.

##### `async add_collection_task(task_id, exchange, symbol, data_type, interval, parameters=None, callback=None)`
Add a new collection task.

**Parameters:**
- `task_id` (str): Unique identifier for the task
- `exchange` (str): Exchange name
- `symbol` (str): Trading pair symbol
- `data_type` (str): Data type ('ohlcv', 'ticker', 'orderbook', 'trades')
- `interval` (int): Collection interval in seconds
- `parameters` (dict, optional): Additional parameters
- `callback` (callable, optional): Callback function for processed data

**Returns:**
- `str`: Task ID

##### `async remove_collection_task(task_id)`
Remove a collection task.

##### `async get_incremental_ohlcv(exchange, symbol, timeframe, since=None)`
Get incremental OHLCV data since last timestamp.

##### `get_collection_status()`
Get current collection system status.

**Returns:**
- `dict`: System status including running tasks and statistics

### OrderBookCollector Class

#### Methods

##### `async add_collection_task(exchange, symbol, depth=20, interval=1.0, priority=1)`
Add an order book collection task.

##### `async get_latest_orderbook(exchange, symbol)`
Get latest order book data from cache.

##### `async get_orderbook_snapshot(exchange, symbol)`
Get current order book snapshot with market metrics.

**Returns:**
- `dict`: Order book snapshot with additional metrics

### TradesCollector Class

#### Methods

##### `async add_collection_task(exchange, symbol, limit=1000, interval=5.0, priority=1, incremental_mode=True)`
Add a trades collection task.

##### `async get_recent_trades(exchange, symbol, limit=50)`
Get recent trade data.

##### `async get_trade_statistics(exchange, symbol, timeframe='1h')`
Get trade statistics for a specific timeframe.

**Returns:**
- `dict`: Trade statistics including volume, price metrics, and ratios

### RedisStorage Class

#### Methods

##### `async cache_market_data(data_type, exchange, symbol, data, ttl=300)`
Cache market data with standardized key format.

##### `async get_cached_market_data(data_type, exchange, symbol)`
Get cached market data.

##### `async cache_ohlcv_data(exchange, symbol, timeframe, ohlcv_data, ttl=300)`
Cache OHLCV data.

##### `async get_cached_ohlcv_data(exchange, symbol, timeframe)`
Get cached OHLCV data.

##### `async cache_quality_score(data_type, exchange, symbol, quality_score, ttl=300)`
Cache quality score.

## Performance Optimization

### Caching Strategy

The system implements a multi-level caching strategy:

1. **Redis Caching**
   - Short-term caching (30s - 5min) for real-time data
   - Medium-term caching (1min - 1hour) for analytics
   - Long-term caching (24hours) for incremental timestamps

2. **In-memory Caching**
   - Active operation tracking
   - Performance metrics
   - Quality alerts

3. **Database Indexing**
   - TimescaleDB hypertables for time-series data
   - Optimized queries for common access patterns

### Load Balancing

The load balancer distributes collection tasks based on:

- **Exchange Load**: Current request rate and response times
- **Task Priority**: Higher priority tasks get preferential treatment
- **Resource Availability**: Connection pool status and memory usage
- **Error Rates**: Exchanges with high error rates get lower priority

### Rate Limiting

Rate limiting prevents API abuse and ensures reliable operation:

- **Per-exchange limits** based on API capabilities
- **Adaptive backoff** for error scenarios
- **Token bucket algorithm** for smooth rate control
- **Circuit breaker** for fault isolation

## Quality Monitoring

### Validation Rules

The system validates data using multiple criteria:

#### OHLCV Data
- Price consistency (high ≥ low ≥ close/open)
- Volume validation (non-negative)
- Timestamp reasonableness
- Price change thresholds

#### Order Book Data
- Bid-ask spread validation
- Price ordering (bids ≤ asks)
- Depth requirements
- Spread percentage thresholds

#### Trades Data
- Price and amount validation
- Side verification (buy/sell)
- Timestamp sequencing
- Trade ID uniqueness

#### Ticker Data
- Price validation
- Bid-ask spread checks
- Volume consistency
- Change percentage reasonableness

### Quality Metrics

- **Accuracy Score**: Data correctness and format validation
- **Completeness Score**: Required field presence and data density
- **Timeliness Score**: Data freshness and latency metrics
- **Overall Score**: Weighted combination of all metrics

### Alert System

Quality alerts are generated when:

- Individual quality scores fall below thresholds
- System-wide quality degrades
- Anomalous patterns are detected
- Exchange-specific issues occur

## Monitoring and Observability

### Metrics Collection

The system collects comprehensive metrics:

#### Collection Metrics
- Total collections by data type
- Success/failure rates
- Data points processed
- Collection duration statistics

#### Quality Metrics
- Quality scores by data type
- Validation error rates
- Anomaly detection counts
- Alert frequency

#### Performance Metrics
- Cache hit/miss ratios
- Connection pool usage
- Rate limiter utilization
- Memory and CPU usage

### Health Checks

Regular health checks monitor:

- **Exchange Connectivity**: API availability and response times
- **Database Health**: Connection status and query performance
- **Cache Health**: Redis connectivity and memory usage
- **System Resources**: Memory, CPU, and disk usage

### Logging

Comprehensive logging includes:

- **Collection Events**: Task start/end, success/failure
- **Quality Events**: Validation results, alerts, threshold breaches
- **Performance Events**: Slow operations, resource constraints
- **System Events**: Initialization, shutdown, errors

## Deployment

### Requirements

- Python 3.8+
- PostgreSQL/TimescaleDB
- Redis
- CCXT library
- AsyncIO support

### Setup

1. **Database Setup**
```bash
# Create TimescaleDB database
createdb timescaledb_crypto
psql -d timescaledb_crypto -c "CREATE EXTENSION timescaledb;"

# Run migrations
python src/data_collection/models/migrate.py
```

2. **Redis Setup**
```bash
# Start Redis server
redis-server

# Verify connection
redis-cli ping
```

3. **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

4. **Running the System**
```python
from src.data_collection.main import main

# Start data collection
await main()
```

### Scaling

#### Horizontal Scaling
- Multiple collector instances with shared Redis
- Database read replicas for query scaling
- Exchange-specific collectors for high-volume symbols

#### Vertical Scaling
- Connection pool tuning
- Memory optimization for caching
- CPU optimization for data processing

#### Load Testing
```python
# Simulate high load
async def load_test():
    collector = DataCollector()
    await collector.start()

    # Add many high-frequency tasks
    for i in range(100):
        await collector.add_collection_task(
            f"load_test_{i}",
            "binance",
            f"BTC/USDT",
            "ticker",
            1
        )

    # Monitor performance
    while True:
        status = collector.get_collection_status()
        print(f"Active tasks: {status['active_tasks']}")
        await asyncio.sleep(5)
```

## Troubleshooting

### Common Issues

#### High Latency
- Check exchange API rate limits
- Monitor network connectivity
- Review database query performance
- Check cache hit rates

#### Data Quality Issues
- Review validation rules and thresholds
- Check exchange data format changes
- Monitor for exchange-specific issues
- Verify data processing logic

#### Memory Usage
- Tune cache sizes and TTL values
- Monitor connection pool usage
- Review data retention policies
- Check for memory leaks

#### Connection Errors
- Verify API credentials and permissions
- Check network connectivity
- Review rate limiting configuration
- Monitor exchange status

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling

Use the built-in performance monitor:
```python
stats = performance_monitor.get_system_performance()
print(f"Average duration: {stats['avg_duration']:.2f}s")
print(f"Success rate: {stats['success_rate']:.2%}")
```

## Best Practices

### Configuration
- Start with conservative rate limits
- Monitor and adjust based on exchange capabilities
- Use appropriate cache TTL values
- Set realistic quality thresholds

### Monitoring
- Set up comprehensive alerting
- Monitor key metrics continuously
- Log all collection events
- Regular health checks

### Error Handling
- Implement proper error recovery
- Use circuit breakers for external services
- Log detailed error information
- Monitor error rates and patterns

### Performance
- Use connection pooling
- Implement proper caching strategies
- Monitor resource usage
- Optimize database queries

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting guide
- Review the API documentation
- Monitor system logs
# News Collection Agent Framework

A comprehensive news collection framework for cryptocurrency news sources, featuring unified adapter interfaces, connection management, health monitoring, and automated failover mechanisms.

## Features

### Core Architecture
- **Adapter Pattern**: Unified interface for all news source adapters
- **Connection Management**: Efficient connection pooling and lifecycle management
- **Health Monitoring**: Real-time health status monitoring with alerts
- **Rate Limiting**: Built-in rate limiting with configurable limits per source
- **Error Handling**: Comprehensive error handling with exponential backoff
- **Failover Mechanism**: Automatic failover when primary sources are unavailable

### Supported News Sources
- **CoinDesk API**: Real-time cryptocurrency news and market analysis
- **CoinTelegraph API**: Comprehensive blockchain and cryptocurrency coverage
- **Decrypt API**: In-depth crypto and technology news
- **Extensible**: Easy to add new news sources

### Key Components
- **NewsManager**: Main orchestrator for news collection
- **ConnectionManager**: Handles connection lifecycle and load balancing
- **HealthMonitor**: Monitors API response times and availability
- **RateLimiter**: Token bucket rate limiting implementation
- **BaseAdapter**: Abstract base class for all news source adapters

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (optional):
```bash
# CoinDesk configuration
COINDESK_API_KEY=your_coindesk_api_key
COINDESK_RATE_LIMIT=60
COINDESK_TIMEOUT=30
COINDESK_ENABLED=true

# CoinTelegraph configuration
COINTELEGRAPH_API_KEY=your_cointelegraph_api_key
COINTELEGRAPH_RATE_LIMIT=60
COINTELEGRAPH_TIMEOUT=30
COINTELEGRAPH_ENABLED=true

# Decrypt configuration
DECRYPT_API_KEY=your_decrypt_api_key
DECRYPT_RATE_LIMIT=60
DECRYPT_TIMEOUT=30
DECRYPT_ENABLED=true
```

## Quick Start

### Basic Usage

```python
import asyncio
from news_collection.news_manager import NewsCollectionManager
from news_collection.models import NewsCategory

async def main():
    # Create and initialize the manager
    manager = NewsCollectionManager()
    await manager.initialize()

    # Fetch latest news
    articles = await manager.fetch_news(limit=10)
    for article in articles:
        print(f"{article.title} - {article.source.value}")

    # Filter by category
    market_news = await manager.fetch_news(
        categories=[NewsCategory.MARKET_NEWS]
    )

    # Search for specific topics
    bitcoin_news = await manager.search_news("bitcoin")

    # Clean up
    await manager.close()

asyncio.run(main())
```

### Automated Collection

```python
# Start automated news collection
await manager.start_collection(interval_seconds=300)  # Every 5 minutes

# Let it run
await asyncio.sleep(3600)  # Run for 1 hour

# Stop collection
await manager.stop_collection()
```

### Direct Adapter Usage

```python
from news_collection.models import NewsSource, NewsSourceType
from news_collection.adapters import CoinDeskAdapter

# Create source configuration
source_config = NewsSource(
    name="CoinDesk",
    source_type=NewsSourceType.COINDESK,
    base_url="https://api.coindesk.com/v1",
    rate_limit_per_minute=60
)

# Create and use adapter
adapter = CoinDeskAdapter(source_config)
await adapter.initialize()

# Fetch news
articles = await adapter.fetch_news(limit=20)

# Test connection
status = await adapter.test_connection()
print(f"Connected: {status.is_connected}")

# Clean up
await adapter.close()
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COINDESK_ENABLED` | Enable CoinDesk adapter | `true` |
| `COINDESK_API_KEY` | CoinDesk API key | `None` |
| `COINDESK_RATE_LIMIT` | Requests per minute | `60` |
| `COINDESK_TIMEOUT` | Request timeout in seconds | `30` |
| `COINTELEGRAPH_ENABLED` | Enable CoinTelegraph adapter | `true` |
| `COINTELEGRAPH_API_KEY` | CoinTelegraph API key | `None` |
| `COINTELEGRAPH_RATE_LIMIT` | Requests per minute | `60` |
| `COINTELEGRAPH_TIMEOUT` | Request timeout in seconds | `30` |
| `DECRYPT_ENABLED` | Enable Decrypt adapter | `true` |
| `DECRYPT_API_KEY` | Decrypt API key | `None` |
| `DECRYPT_RATE_LIMIT` | Requests per minute | `60` |
| `DECRYPT_TIMEOUT` | Request timeout in seconds | `30` |

### Custom Configuration

```python
config = {
    "sources": [
        {
            "name": "Custom Source",
            "source_type": NewsSourceType.COINDESK,
            "base_url": "https://api.custom.com",
            "api_key": "your_api_key",
            "rate_limit_per_minute": 100,
            "timeout_seconds": 45,
            "enabled": True,
            "priority": 1,
            "config": {
                "custom_param": "value"
            }
        }
    ]
}

await manager.initialize(config)
```

## API Reference

### NewsCollectionManager

Main class for managing news collection from multiple sources.

#### Methods

- `initialize(config=None)`: Initialize the manager with configuration
- `start_collection(interval_seconds=300)`: Start automated collection
- `stop_collection()`: Stop automated collection
- `fetch_news(limit=10, sources=None, categories=None, keywords=None, since=None)`: Fetch news with filters
- `search_news(query, limit=10)`: Search for news articles
- `get_connection_status()`: Get connection status for all sources
- `get_health_summary()`: Get health summary for all sources
- `get_health_metrics()`: Get detailed health metrics
- `test_source_connection(source_name)`: Test connection to specific source
- `restart_source(source_name)`: Restart a specific source
- `close()`: Clean up resources

### NewsArticle

Represents a single news article.

#### Fields

- `id`: Unique identifier
- `title`: Article title
- `content`: Article content
- `summary`: Article summary (optional)
- `url`: Article URL
- `author`: Article author (optional)
- `published_at`: Publication datetime
- `source`: News source type
- `category`: News category
- `tags`: List of tags
- `sentiment_score`: Sentiment analysis score (optional)
- `relevance_score`: Relevance score (optional)
- `metadata`: Additional metadata

### NewsCategory

Enum of supported news categories:

- `MARKET_NEWS`: Market analysis and price movements
- `TECHNOLOGY`: Blockchain and technology developments
- `REGULATION`: Regulatory and legal news
- `SECURITY`: Security and vulnerability reports
- `ADOPTION`: Mainstream and institutional adoption
- `DEFI`: DeFi protocol and ecosystem news
- `NFT`: NFT and digital collectibles
- `EXCHANGE`: Exchange and platform news
- `MINING`: Mining and hardware developments
- `TRADING`: Trading and investment strategies

### NewsSourceType

Enum of supported news sources:

- `COINDESK`: CoinDesk news API
- `COINTELEGRAPH`: CoinTelegraph news API
- `DECRYPT`: Decrypt news API
- `CRYPTOSLATE`: CryptoSlate news API (planned)
- `THE_BLOCK`: The Block news API (planned)

## Health Monitoring

The framework includes comprehensive health monitoring with:

- **Connection Status**: Real-time connection status monitoring
- **Response Time Tracking**: Average and current response times
- **Uptime Monitoring**: Uptime percentage calculation
- **Error Tracking**: Consecutive failure counting
- **Alert System**: Configurable alerts for health issues

### Health Alerts

```python
# Get active alerts
alerts = manager.get_active_alerts()
for alert in alerts:
    print(f"{alert.severity}: {alert.source_name} - {alert.message}")

# Add custom alert callback
def handle_alert(alert):
    print(f"ALERT: {alert.message}")

manager.health_monitor.add_alert_callback(handle_alert)
```

## Rate Limiting

Built-in rate limiting using token bucket algorithm:

- **Per-source limits**: Configurable rate limits per news source
- **Automatic throttling**: Automatically waits when limits are reached
- **Request tracking**: Tracks remaining requests and reset times

```python
# Check rate limit info
adapter = await manager.connection_manager.get_adapter("CoinDesk")
rate_info = await adapter.get_rate_limit_info()
print(f"Remaining: {rate_info.requests_remaining}/{rate_info.requests_limit}")
```

## Error Handling

Comprehensive error handling includes:

- **Connection Failures**: Automatic retry with exponential backoff
- **Rate Limiting**: Respect API rate limits and retry appropriately
- **Timeout Handling**: Configurable timeouts for all requests
- **Data Validation**: Validate and sanitize API responses
- **Graceful Degradation**: Continue working with available sources

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_adapters.py

# Run with coverage
python -m pytest tests/ --cov=news_collection
```

### Example Test

```python
import pytest
from news_collection.models import NewsArticle, NewsCategory, NewsSourceType

def test_news_article_creation():
    article = NewsArticle(
        id="test_123",
        title="Test Article",
        content="Test content",
        url="https://test.com"
    )

    assert article.id == "test_123"
    assert article.title == "Test Article"
    assert article.category == NewsCategory.MARKET_NEWS
```

## Performance

### Benchmarks

- **Connection Time**: <5 seconds for new connections
- **Response Time**: <2 seconds for individual requests
- **Health Check Overhead**: <1% of system resources
- **Concurrent Connections**: Support for 10+ concurrent connections
- **Requests per Minute**: Support for 1000+ requests per minute
- **Failover Time**: <1 minute detection and recovery

### Optimization Tips

1. **Rate Limits**: Configure appropriate rate limits for your API keys
2. **Timeouts**: Set reasonable timeouts based on your network conditions
3. **Collection Interval**: Balance between freshness and resource usage
4. **Health Check Interval**: Adjust based on your monitoring needs
5. **Connection Pool**: Reuse connections when possible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Adding New Adapters

To add a new news source adapter:

1. Create a new adapter class inheriting from `BaseNewsAdapter`
2. Implement required methods: `fetch_news`, `test_connection`, `get_rate_limit_info`, `_parse_article`
3. Register the adapter in the `NewsCollectionManager`
4. Add appropriate tests
5. Update documentation

Example:
```python
class NewSourceAdapter(BaseNewsAdapter):
    @property
    def source_name(self):
        return "New Source"

    @property
    def supported_categories(self):
        return [NewsCategory.MARKET_NEWS]

    async def fetch_news(self, **kwargs):
        # Implementation
        pass

    # ... other required methods
```

## License

This project is part of the Crypto Trading Multi Agents system.

## Support

For issues and questions:
- Check the existing issues on GitHub
- Create a new issue with detailed description
- Include error logs and reproduction steps
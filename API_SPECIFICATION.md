# Long Analyst Agent API Specification

## Overview

This document provides the complete API specification for the Long Analyst Agent, including REST endpoints, WebSocket interfaces, and data schemas for external integration.

## Base URL

```
Production: https://api.longanalyst.example.com/v1
Development: http://localhost:8000/v1
```

## Authentication

All API requests require authentication using API keys in the Authorization header:

```
Authorization: Bearer <your-api-key>
```

## REST API Endpoints

### 1. Analysis Endpoints

#### POST /analyze/symbol
Perform comprehensive analysis for a single symbol.

**Request Body:**
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "include_technical": true,
  "include_fundamental": true,
  "include_sentiment": true,
  "include_llm": true,
  "analysis_depth": "comprehensive"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC/USDT",
    "analysis_id": "analysis_123456",
    "timestamp": 1634567890,
    "signals": [
      {
        "id": "signal_789012",
        "type": "strong_buy",
        "strength": 0.85,
        "confidence": 0.78,
        "entry_price": 45000.0,
        "stop_loss": 44000.0,
        "take_profit": 47000.0,
        "reasoning": "Strong uptrend confirmed by multiple indicators",
        "timeframe": "1h",
        "expiry": 1634571490
      }
    ],
    "analysis_summary": {
      "technical_score": 0.82,
      "fundamental_score": 0.75,
      "sentiment_score": 0.68,
      "llm_score": 0.80,
      "overall_score": 0.77,
      "confidence": 0.76,
      "risk_level": 0.35
    },
    "performance_metrics": {
      "processing_time_ms": 342,
      "data_sources_used": 3,
      "indicators_calculated": 24
    }
  },
  "metadata": {
    "request_id": "req_123456",
    "api_version": "v1.0.0",
    "timestamp": 1634567890
  }
}
```

#### POST /analyze/batch
Perform batch analysis for multiple symbols.

**Request Body:**
```json
{
  "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],
  "timeframes": ["1h", "4h", "1d"],
  "analysis_options": {
    "include_technical": true,
    "include_fundamental": true,
    "include_sentiment": true,
    "include_llm": false
  },
  "priority": "normal"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_789012",
    "total_symbols": 3,
    "completed_analyses": 3,
    "results": {
      "BTC/USDT": {
        "signals": [...],
        "analysis_summary": {...}
      },
      "ETH/USDT": {
        "signals": [...],
        "analysis_summary": {...}
      },
      "BNB/USDT": {
        "signals": [...],
        "analysis_summary": {...}
      }
    },
    "batch_summary": {
      "total_signals_generated": 7,
      "average_score": 0.72,
      "processing_time_ms": 1256
    }
  }
}
```

### 2. Signal Management

#### GET /signals
Retrieve current active signals.

**Query Parameters:**
- `symbol` (optional): Filter by symbol
- `type` (optional): Filter by signal type
- `min_strength` (optional): Minimum signal strength
- `min_confidence` (optional): Minimum confidence level
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "signals": [
      {
        "id": "signal_123456",
        "symbol": "BTC/USDT",
        "type": "buy",
        "strength": 0.75,
        "confidence": 0.68,
        "entry_price": 45000.0,
        "stop_loss": 44200.0,
        "take_profit": 46500.0,
        "timestamp": 1634567890,
        "expiry": 1634571490,
        "sources": [
          {
            "category": "technical",
            "name": "trend_analysis",
            "confidence": 0.72,
            "weight": 0.4
          },
          {
            "category": "sentiment",
            "name": "social_media",
            "confidence": 0.65,
            "weight": 0.2
          }
        ],
        "risk_metrics": {
          "risk_level": 0.32,
          "win_probability": 0.68,
          "expected_return": 3.33,
          "max_drawdown": 2.2
        }
      }
    ],
    "pagination": {
      "total": 1,
      "limit": 100,
      "offset": 0
    }
  }
}
```

#### GET /signals/{signal_id}
Get details of a specific signal.

**Response:**
```json
{
  "success": true,
  "data": {
    "signal": {
      "id": "signal_123456",
      "symbol": "BTC/USDT",
      "type": "buy",
      "strength": 0.75,
      "confidence": 0.68,
      "timestamp": 1634567890,
      "analysis_details": {
        "technical_indicators": {
          "rsi": 45.2,
          "macd": 125.3,
          "bollinger_position": "middle",
          "volume_ratio": 1.4
        },
        "fundamental_metrics": {
          "market_cap": 850000000000,
          "active_addresses": 1250000,
          "development_score": 8.5
        },
        "sentiment_metrics": {
          "social_sentiment": 0.72,
          "news_sentiment": 0.68,
          "fear_greed_index": 58
        },
        "llm_analysis": {
          "market_context": "Bullish momentum with strong technical confirmation",
          "investment_thesis": "Favorable risk-reward ratio for long position",
          "key_levels": [44000, 46500, 48500]
        }
      }
    }
  }
}
```

#### POST /signals/trigger
Manually trigger a signal execution.

**Request Body:**
```json
{
  "signal_id": "signal_123456",
  "execution_price": 45050.0,
  "position_size": 0.1,
  "notes": "Manual execution based on market conditions"
}
```

### 3. Performance Analytics

#### GET /analytics/performance
Get system performance metrics.

**Query Parameters:**
- `timeframe` (optional): Time window (1h, 24h, 7d, 30d, 90d, 1y)
- `metrics` (optional): Comma-separated list of metrics

**Response:**
```json
{
  "success": true,
  "data": {
    "timeframe": "24h",
    "metrics": {
      "total_signals_generated": 156,
      "successful_signals": 108,
      "win_rate": 0.692,
      "average_return": 2.45,
      "total_return": 382.2,
      "sharpe_ratio": 2.34,
      "max_drawdown": 8.7,
      "profit_factor": 2.1,
      "risk_adjusted_return": 0.28
    },
    "signal_performance": {
      "strong_buy": {
        "count": 45,
        "win_rate": 0.78,
        "avg_return": 3.2
      },
      "buy": {
        "count": 67,
        "win_rate": 0.65,
        "avg_return": 2.1
      },
      "moderate_buy": {
        "count": 44,
        "win_rate": 0.61,
        "avg_return": 1.8
      }
    },
    "system_metrics": {
      "uptime_seconds": 86400,
      "average_latency_ms": 342,
      "error_rate": 0.003,
      "active_connections": 127,
      "memory_usage_mb": 2048,
      "cpu_usage_percent": 45.2
    }
  }
}
```

#### GET /analytics/win-rate
Get detailed win rate analysis.

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_win_rate": 0.685,
    "win_rate_by_type": {
      "strong_buy": 0.78,
      "buy": 0.65,
      "moderate_buy": 0.61,
      "hold": 0.52
    },
    "win_rate_by_timeframe": {
      "1m": 0.62,
      "5m": 0.65,
      "15m": 0.67,
      "1h": 0.69,
      "4h": 0.71,
      "1d": 0.74
    },
    "win_rate_by_symbol": {
      "BTC/USDT": 0.72,
      "ETH/USDT": 0.68,
      "BNB/USDT": 0.65,
      "SOL/USDT": 0.70
    },
    "risk_adjusted_performance": {
      "high_risk": {
        "win_rate": 0.45,
        "avg_return": 4.2,
        "sharpe_ratio": 1.2
      },
      "medium_risk": {
        "win_rate": 0.68,
        "avg_return": 2.3,
        "sharpe_ratio": 2.1
      },
      "low_risk": {
        "win_rate": 0.82,
        "avg_return": 1.4,
        "sharpe_ratio": 2.8
      }
    }
  }
}
```

### 4. Market Data

#### GET /market/data
Get current market data for a symbol.

**Query Parameters:**
- `symbol`: Trading symbol (required)
- `timeframe`: Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `limit`: Number of data points (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "current_data": {
      "timestamp": 1634567890,
      "open": 44800.0,
      "high": 45200.0,
      "low": 44750.0,
      "close": 45000.0,
      "volume": 1250000000,
      "quote_volume": 56250000000000
    },
    "historical_data": [
      {
        "timestamp": 1634564290,
        "open": 44600.0,
        "high": 44850.0,
        "low": 44500.0,
        "close": 44800.0,
        "volume": 1180000000
      }
    ],
    "market_summary": {
      "price_change_24h": 2.34,
      "price_change_percent_24h": 5.48,
      "volume_24h": 28500000000,
      "market_cap": 850000000000,
      "dominance": 45.2
    }
  }
}
```

#### GET /market/tickers
Get market tickers for multiple symbols.

**Query Parameters:**
- `symbols`: Comma-separated list of symbols

**Response:**
```json
{
  "success": true,
  "data": {
    "tickers": [
      {
        "symbol": "BTC/USDT",
        "last_price": 45000.0,
        "bid_price": 44998.5,
        "ask_price": 45001.5,
        "volume_24h": 28500000000,
        "price_change_24h": 1250.0,
        "price_change_percent_24h": 2.86,
        "high_24h": 45800.0,
        "low_24h": 44200.0,
        "market_cap": 850000000000
      }
    ]
  }
}
```

### 5. System Management

#### GET /system/health
Get system health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": 1634567890,
    "components": {
      "analysis_engine": {
        "status": "healthy",
        "uptime": 86400,
        "last_analysis": 1634567885,
        "error_rate": 0.002
      },
      "data_manager": {
        "status": "healthy",
        "data_sources": 3,
        "last_update": 1634567890,
        "cache_hit_rate": 0.85
      },
      "llm_engine": {
        "status": "healthy",
        "api_status": "connected",
        "response_time_ms": 245,
        "cache_size": 1250
      },
      "signal_evaluator": {
        "status": "healthy",
        "signals_processed": 156,
        "approval_rate": 0.68,
        "avg_evaluation_time_ms": 45
      },
      "storage": {
        "status": "healthy",
        "database_connected": true,
        "cache_connected": true,
        "disk_usage_percent": 65.4
      }
    },
    "performance": {
      "cpu_usage_percent": 42.3,
      "memory_usage_mb": 2048,
      "disk_usage_mb": 51200,
      "network_io_mbps": 125.4,
      "active_connections": 127
    }
  }
}
```

#### GET /system/metrics
Get detailed system metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "uptime_seconds": 86400,
    "version": "1.0.0",
    "build_timestamp": "2024-01-15T10:30:00Z",
    "metrics": {
      "api_requests_total": 15420,
      "api_requests_per_second": 0.178,
      "analysis_requests_total": 3420,
      "analysis_success_rate": 0.995,
      "average_analysis_time_ms": 342,
      "signals_generated_total": 156,
      "signal_quality_score": 0.72,
      "error_rate_24h": 0.003,
      "cache_hit_rate": 0.85,
      "database_connections": 12,
      "redis_connections": 5
    }
  }
}
```

#### POST /system/config
Update system configuration.

**Request Body:**
```json
{
  "analysis_settings": {
    "enable_technical_analysis": true,
    "enable_fundamental_analysis": true,
    "enable_sentiment_analysis": true,
    "enable_llm_analysis": true,
    "min_signal_strength": 0.6,
    "min_confidence": 0.7
  },
  "performance_settings": {
    "max_concurrent_requests": 1000,
    "analysis_timeout_ms": 5000,
    "cache_ttl_seconds": 300
  },
  "risk_management": {
    "max_risk_level": 0.8,
    "min_win_rate": 0.6,
    "max_position_size": 0.1
  }
}
```

## WebSocket API

### Real-time Signal Stream

**Endpoint:** `wss://api.longanalyst.example.com/v1/ws/signals`

**Connection:**
```javascript
const ws = new WebSocket('wss://api.longanalyst.example.com/v1/ws/signals?token=your-api-key');

ws.onopen = () => {
  // Subscribe to specific symbols
  ws.send(JSON.stringify({
    "action": "subscribe",
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "signal_types": ["buy", "strong_buy"]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New signal:', data);
};
```

**Message Format:**
```json
{
  "type": "signal",
  "timestamp": 1634567890,
  "data": {
    "id": "signal_123456",
    "symbol": "BTC/USDT",
    "signal_type": "strong_buy",
    "strength": 0.85,
    "confidence": 0.78,
    "entry_price": 45000.0,
    "stop_loss": 44200.0,
    "take_profit": 46500.0,
    "reasoning": "Strong technical indicators confirm uptrend"
  }
}
```

### Market Data Stream

**Endpoint:** `wss://api.longanalyst.example.com/v1/ws/market`

**Subscription Message:**
```json
{
  "action": "subscribe",
  "symbols": ["BTC/USDT"],
  "timeframes": ["1m", "5m", "1h"],
  "data_types": ["ticker", "trades", "orderbook"]
}
```

**Market Data Message:**
```json
{
  "type": "ticker",
  "symbol": "BTC/USDT",
  "timestamp": 1634567890,
  "data": {
    "last_price": 45000.0,
    "bid": 44998.5,
    "ask": 45001.5,
    "volume_24h": 28500000000,
    "price_change_24h": 1250.0,
    "price_change_percent_24h": 2.86
  }
}
```

## Data Models

### Signal Model
```typescript
interface Signal {
  id: string;
  symbol: string;
  signal_type: 'strong_buy' | 'buy' | 'moderate_buy' | 'hold' | 'sell' | 'strong_sell';
  strength: number; // 0.0 to 1.0
  confidence: number; // 0.0 to 1.0
  entry_price: number;
  stop_loss?: number;
  take_profit?: number;
  timeframe: string;
  timestamp: number;
  expiry: number;
  sources: SignalSource[];
  risk_metrics: RiskMetrics;
  reasoning: string;
}

interface SignalSource {
  category: 'technical' | 'fundamental' | 'sentiment' | 'llm_enhanced';
  name: string;
  confidence: number;
  weight: number;
}

interface RiskMetrics {
  risk_level: number; // 0.0 to 1.0
  win_probability: number; // 0.0 to 1.0
  expected_return: number; // percentage
  max_drawdown: number; // percentage
}
```

### Analysis Result Model
```typescript
interface AnalysisResult {
  id: string;
  symbol: string;
  dimension: 'technical' | 'fundamental' | 'sentiment' | 'llm' | 'combined';
  score: number; // 0.0 to 1.0
  confidence: number; // 0.0 to 1.0
  timestamp: number;
  timeframe: string;
  technical_indicators?: TechnicalIndicators;
  fundamental_metrics?: FundamentalMetrics;
  sentiment_metrics?: SentimentMetrics;
  llm_analysis?: LLMAnalysis;
  signals: string[];
  recommendations: string[];
}

interface TechnicalIndicators {
  trend_indicators: {
    sma_20?: number;
    sma_50?: number;
    sma_200?: number;
    ema_12?: number;
    ema_26?: number;
  };
  momentum_indicators: {
    rsi?: number;
    macd?: number;
    stochastic?: number;
  };
  volatility_indicators: {
    bollinger_upper?: number;
    bollinger_lower?: number;
    atr?: number;
  };
}

interface FundamentalMetrics {
  market_cap?: number;
  circulating_supply?: number;
  active_addresses?: number;
  development_score?: number;
  network_value?: number;
}

interface SentimentMetrics {
  social_sentiment?: number;
  news_sentiment?: number;
  fear_greed_index?: number;
  social_volume?: number;
  whale_activity?: number;
}
```

### Performance Metrics Model
```typescript
interface PerformanceMetrics {
  timeframe: string;
  total_signals: number;
  winning_signals: number;
  losing_signals: number;
  win_rate: number;
  average_return: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  profit_factor: number;
  risk_adjusted_return: number;
  signal_performance: {
    [signal_type: string]: {
      count: number;
      win_rate: number;
      avg_return: number;
    };
  };
}
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Symbol 'INVALID/USDT' is not supported",
    "details": {
      "supported_symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    },
    "timestamp": 1634567890,
    "request_id": "req_123456"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Rate Limiting

- **Standard Tier**: 100 requests per minute
- **Premium Tier**: 1000 requests per minute
- **Enterprise Tier**: Custom limits

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567950
```

## SDKs

### Python SDK
```python
from long_analyst import LongAnalystClient

# Initialize client
client = LongAnalystClient(api_key="your-api-key")

# Analyze symbol
analysis = client.analyze_symbol("BTC/USDT", timeframe="1h")
print(f"Generated {len(analysis.signals)} signals")

# Get performance metrics
performance = client.get_performance(timeframe="7d")
print(f"Win rate: {performance.win_rate:.2%}")

# WebSocket connection
def on_signal(signal):
    print(f"New {signal.signal_type} signal for {signal.symbol}")

client.subscribe_to_signals(["BTC/USDT"], on_signal)
```

### JavaScript SDK
```javascript
import { LongAnalystClient } from 'long-analyst-sdk';

// Initialize client
const client = new LongAnalystClient('your-api-key');

// Analyze symbol
const analysis = await client.analyzeSymbol('BTC/USDT', { timeframe: '1h' });
console.log(`Generated ${analysis.signals.length} signals`);

// Get performance metrics
const performance = await client.getPerformance({ timeframe: '7d' });
console.log(`Win rate: ${(performance.win_rate * 100).toFixed(1)}%`);

// WebSocket connection
client.on('signal', (signal) => {
  console.log(`New ${signal.signal_type} signal for ${signal.symbol}`);
});

await client.connect();
```

## Webhooks

### Configure Webhook
```json
POST /webhooks
{
  "url": "https://your-webhook-endpoint.com/signals",
  "events": ["signal.generated", "analysis.completed"],
  "secret": "your-webhook-secret"
}
```

### Webhook Payload
```json
{
  "event": "signal.generated",
  "timestamp": 1634567890,
  "data": {
    "signal_id": "signal_123456",
    "symbol": "BTC/USDT",
    "signal_type": "strong_buy",
    "strength": 0.85,
    "confidence": 0.78
  },
  "signature": "sha256=abc123..."
}
```

## Monitoring and Logging

### Log Levels
- `ERROR`: System errors and failures
- `WARN`: Warning conditions
- `INFO`: General information
- `DEBUG`: Debug information

### Monitoring Endpoints
- `/health`: System health status
- `/metrics`: Prometheus metrics
- `/logs`: Application logs (requires authentication)

## Security Considerations

1. **API Key Security**
   - Use environment variables for API keys
   - Rotate keys regularly
   - Use different keys for different environments

2. **Data Validation**
   - Validate all input parameters
   - Sanitize user inputs
   - Use parameterized queries

3. **Rate Limiting**
   - Implement per-client rate limits
   - Use sliding window algorithm
   - Provide clear error messages

4. **HTTPS Only**
   - All communications must use HTTPS
   - Use TLS 1.3 or higher
   - Implement HSTS

5. **Audit Logging**
   - Log all API requests
   - Include request IDs for tracing
   - Regular security audits

## Versioning

The API uses semantic versioning (e.g., `v1.0.0`). Breaking changes will result in a new major version.

### Deprecation Policy
- Minor versions may add new features
- Patch versions include bug fixes
- Major versions may include breaking changes
- Deprecated features will be supported for at least 6 months

## Support

For API support and questions:
- Documentation: https://docs.longanalyst.example.com
- Support Email: support@longanalyst.example.com
- Status Page: https://status.longanalyst.example.com
- Community: https://community.longanalyst.example.com
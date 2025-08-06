# API 文档

## 📖 概述

Crypto Trading Agents 提供了丰富的API接口，用于数据获取、分析执行、结果查询等功能。本文档详细描述了所有可用的API接口。

## 🔑 认证

大多数API接口需要API密钥认证：

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
```

## 📊 数据源API

### CoinGecko API

#### 获取价格数据
```python
GET /api/v1/simple/price

参数:
- ids: 币种ID (例如: bitcoin, ethereum)
- vs_currencies: 计价货币 (例如: usd, btc)
- include_24hr_change: 是否包含24小时变化 (true/false)

示例:
GET /api/v1/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true

响应:
{
    "bitcoin": {
        "usd": 50000.0,
        "usd_24h_change": 2.5
    }
}
```

#### 获取市场数据
```python
GET /api/v1/coins/markets

参数:
- vs_currency: 计价货币
- ids: 币种ID列表
- order: 排序方式
- per_page: 每页数量
- page: 页码

示例:
GET /api/v1/coins/markets?vs_currency=usd&ids=bitcoin&order=market_cap_desc

响应:
[
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 50000.0,
        "market_cap": 950000000000,
        "total_volume": 25000000000
    }
]
```

### Glassnode API

#### 获取链上指标
```python
GET /api/v1/metrics

参数:
- a: 资产符号 (例如: BTC)
- i: 时间间隔 (例如: 24h)
- c: 货币单位

示例:
GET /api/v1/metrics?a=BTC&i=24h&=USD

响应:
{
    "active_addresses": 1000000,
    "transaction_count": 500000,
    "market_cap_to_thermocap_ratio": 0.001
}
```

### DeFiLlama API

#### 获取TVL数据
```python
GET /api/v1/protocols

参数:
- chain: 区块链名称 (可选)

示例:
GET /api/v1/protocols?chain=Ethereum

响应:
[
    {
        "name": "Aave",
        "tvl": 10000000000,
        "chain": "Ethereum",
        "category": "Lending"
    }
]
```

## 💹 交易所API

### Binance API

#### 获取交易对信息
```python
GET /api/v3/exchangeInfo

响应:
{
    "timezone": "UTC",
    "serverTime": 1640995200000,
    "symbols": [
        {
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT"
        }
    ]
}
```

#### 获取K线数据
```python
GET /api/v3/klines

参数:
- symbol: 交易对符号
- interval: 时间间隔
- limit: 限制数量
- startTime: 开始时间
- endTime: 结束时间

示例:
GET /api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100

响应:
[
    [
        1640995200000,  // 开盘时间
        50000.0,        // 开盘价
        51000.0,        // 最高价
        49000.0,        // 最低价
        50500.0,        // 收盘价
        1000.0,         // 交易量
        1640998800000,  // 收盘时间
        50500000.0,     // 成交额
        1000,           // 交易笔数
        50500000.0,     // 主动买入成交额
        500             // 主动买入笔数
    ]
]
```

#### 获取深度数据
```python
GET /api/v3/depth

参数:
- symbol: 交易对符号
- limit: 限制数量

示例:
GET /api/v3/depth?symbol=BTCUSDT&limit=100

响应:
{
    "lastUpdateId": 123456,
    "bids": [
        ["50000.0", "1.5"],  // 价格, 数量
        ["49900.0", "2.0"]
    ],
    "asks": [
        ["50100.0", "1.0"],
        ["50200.0", "1.8"]
    ]
}
```

### Coinbase API

#### 获取产品信息
```python
GET /products

响应:
[
    {
        "id": "BTC-USD",
        "base_currency": "BTC",
        "quote_currency": "USD",
        "base_min_size": "0.001",
        "base_max_size": "280",
        "quote_increment": "0.01"
    }
]
```

#### 获取行情数据
```python
GET /products/{product_id}/ticker

示例:
GET /products/BTC-USD/ticker

响应:
{
    "trade_id": 123456,
    "price": "50000.00",
    "size": "0.1",
    "bid": "49900.00",
    "ask": "50100.00",
    "volume": "1000.0",
    "time": "2022-01-01T00:00:00.000Z"
}
```

## 🤖 分析代理API

### 技术分析API

#### 执行技术分析
```python
POST /api/v1/analysis/technical

请求体:
{
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "indicators": ["rsi", "macd", "bollinger_bands"],
    "limit": 100
}

响应:
{
    "analysis_id": "tech_123456",
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "indicators": {
        "rsi": {
            "value": 65.5,
            "signal": "neutral",
            "overbought": false,
            "oversold": false
        },
        "macd": {
            "macd": 150.5,
            "signal": 140.2,
            "histogram": 10.3,
            "signal": "bullish"
        },
        "bollinger_bands": {
            "upper": 52000.0,
            "middle": 50000.0,
            "lower": 48000.0,
            "position": "middle",
            "signal": "neutral"
        }
    },
    "overall_signal": "bullish",
    "confidence": 0.75
}
```

### 链上分析API

#### 执行链上分析
```python
POST /api/v1/analysis/onchain

请求体:
{
    "symbol": "BTC/USDT",
    "metrics": ["active_addresses", "transaction_count", "whale_activity"],
    "timeframe": "24h"
}

响应:
{
    "analysis_id": "onchain_123456",
    "symbol": "BTC/USDT",
    "metrics": {
        "active_addresses": {
            "current": 1000000,
            "change_24h": 5.2,
            "trend": "increasing",
            "signal": "bullish"
        },
        "transaction_count": {
            "current": 500000,
            "change_24h": 3.1,
            "trend": "stable",
            "signal": "neutral"
        },
        "whale_activity": {
            "large_transactions": 100,
            "change_24h": -2.5,
            "trend": "decreasing",
            "signal": "bearish"
        }
    },
    "overall_signal": "neutral",
    "confidence": 0.65
}
```

### 情绪分析API

#### 执行情绪分析
```python
POST /api/v1/analysis/sentiment

请求体:
{
    "symbol": "BTC/USDT",
    "sources": ["twitter", "reddit", "news"],
    "timeframe": "24h"
}

响应:
{
    "analysis_id": "sentiment_123456",
    "symbol": "BTC/USDT",
    "sources": {
        "twitter": {
            "sentiment_score": 0.65,
            "mention_count": 10000,
            "trend": "positive",
            "signal": "bullish"
        },
        "reddit": {
            "sentiment_score": 0.55,
            "mention_count": 5000,
            "trend": "neutral",
            "signal": "neutral"
        },
        "news": {
            "sentiment_score": 0.70,
            "article_count": 100,
            "trend": "positive",
            "signal": "bullish"
        }
    },
    "overall_signal": "bullish",
    "confidence": 0.70
}
```

### DeFi分析API

#### 执行DeFi分析
```python
POST /api/v1/analysis/defi

请求体:
{
    "symbol": "BTC/USDT",
    "protocols": ["aave", "compound", "uniswap"],
    "timeframe": "24h"
}

响应:
{
    "analysis_id": "defi_123456",
    "symbol": "BTC/USDT",
    "protocols": {
        "aave": {
            "tvl": 10000000000,
            "change_24h": 2.5,
            "apy": 5.2,
            "signal": "bullish"
        },
        "compound": {
            "tvl": 5000000000,
            "change_24h": 1.8,
            "apy": 4.8,
            "signal": "neutral"
        },
        "uniswap": {
            "tvl": 3000000000,
            "change_24h": 3.2,
            "volume_24h": 100000000,
            "signal": "bullish"
        }
    },
    "overall_signal": "bullish",
    "confidence": 0.68
}
```

### 综合分析API

#### 执行综合分析
```python
POST /api/v1/analysis/comprehensive

请求体:
{
    "symbol": "BTC/USDT",
    "agents": ["technical", "onchain", "sentiment", "defi"],
    "timeframe": "1h",
    "depth": 3,
    "risk_level": "medium"
}

响应:
{
    "analysis_id": "comprehensive_123456",
    "symbol": "BTC/USDT",
    "agents": ["technical", "onchain", "sentiment", "defi"],
    "start_time": "2022-01-01T00:00:00.000Z",
    "end_time": "2022-01-01T00:05:00.000Z",
    "status": "completed",
    "results": {
        "technical": {
            "signal": "bullish",
            "confidence": 0.75,
            "details": {...}
        },
        "onchain": {
            "signal": "neutral",
            "confidence": 0.65,
            "details": {...}
        },
        "sentiment": {
            "signal": "bullish",
            "confidence": 0.70,
            "details": {...}
        },
        "defi": {
            "signal": "bullish",
            "confidence": 0.68,
            "details": {...}
        }
    },
    "overall_signal": "bullish",
    "overall_confidence": 0.70,
    "recommendation": "BUY",
    "risk_assessment": {
        "risk_level": "medium",
        "potential_return": 0.15,
        "stop_loss": 0.05,
        "take_profit": 0.20
    }
}
```

## 📈 结果查询API

### 获取分析结果
```python
GET /api/v1/analysis/{analysis_id}

示例:
GET /api/v1/analysis/comprehensive_123456

响应:
{
    "analysis_id": "comprehensive_123456",
    "symbol": "BTC/USDT",
    "status": "completed",
    "progress": 100,
    "created_at": "2022-01-01T00:00:00.000Z",
    "updated_at": "2022-01-01T00:05:00.000Z",
    "results": {...}
}
```

### 获取分析进度
```python
GET /api/v1/analysis/{analysis_id}/progress

示例:
GET /api/v1/analysis/comprehensive_123456/progress

响应:
{
    "analysis_id": "comprehensive_123456",
    "status": "running",
    "progress": 65,
    "current_step": "sentiment_analysis",
    "total_steps": 10,
    "estimated_completion": "2022-01-01T00:08:00.000Z",
    "messages": [
        {
            "timestamp": "2022-01-01T00:02:00.000Z",
            "message": "开始技术分析"
        },
        {
            "timestamp": "2022-01-01T00:04:00.000Z",
            "message": "技术分析完成"
        }
    ]
}
```

### 获取分析历史
```python
GET /api/v1/analysis/history

参数:
- symbol: 交易对符号 (可选)
- agent: 代理类型 (可选)
- limit: 限制数量 (默认: 50)
- offset: 偏移量 (默认: 0)

示例:
GET /api/v1/analysis/history?symbol=BTC/USDT&limit=10

响应:
{
    "total": 100,
    "limit": 10,
    "offset": 0,
    "analyses": [
        {
            "analysis_id": "comprehensive_123456",
            "symbol": "BTC/USDT",
            "status": "completed",
            "overall_signal": "bullish",
            "created_at": "2022-01-01T00:00:00.000Z"
        }
    ]
}
```

## 🗃️ 数据管理API

### 导出分析结果
```python
GET /api/v1/export/{analysis_id}

参数:
- format: 导出格式 (json, markdown, csv)

示例:
GET /api/v1/export/comprehensive_123456?format=json

响应:
JSON格式的分析结果文件
```

### 删除分析结果
```python
DELETE /api/v1/analysis/{analysis_id}

示例:
DELETE /api/v1/analysis/comprehensive_123456

响应:
{
    "success": true,
    "message": "分析结果已删除"
}
```

### 批量删除
```python
DELETE /api/v1/analysis/batch

请求体:
{
    "analysis_ids": ["id1", "id2", "id3"]
}

响应:
{
    "success": true,
    "deleted_count": 3,
    "failed_count": 0
}
```

## ⚙️ 配置管理API

### 获取系统配置
```python
GET /api/v1/config

响应:
{
    "version": "1.0.0",
    "supported_symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"],
    "available_agents": ["technical", "onchain", "sentiment", "defi"],
    "default_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
    "risk_levels": ["low", "medium", "high"]
}
```

### 更新配置
```python
PUT /api/v1/config

请求体:
{
    "default_timeframe": "1h",
    "risk_level": "medium",
    "notification_enabled": true
}

响应:
{
    "success": true,
    "message": "配置已更新"
}
```

### 获取API状态
```python
GET /api/v1/status

响应:
{
    "status": "healthy",
    "timestamp": "2022-01-01T00:00:00.000Z",
    "uptime": 86400,
    "version": "1.0.0",
    "data_sources": {
        "coingecko": "healthy",
        "binance": "healthy",
        "glassnode": "degraded"
    },
    "active_analyses": 5,
    "queue_length": 2
}
```

## 🔐 认证和权限API

### 获取API密钥
```python
POST /api/v1/auth/api-key

请求体:
{
    "email": "user@example.com",
    "password": "password123"
}

响应:
{
    "api_key": "sk_1234567890abcdef",
    "expires_at": "2023-01-01T00:00:00.000Z"
}
```

### 刷新API密钥
```python
POST /api/v1/auth/refresh

请求体:
{
    "api_key": "sk_1234567890abcdef"
}

响应:
{
    "api_key": "sk_0987654321fedcba",
    "expires_at": "2023-01-01T00:00:00.000Z"
}
```

### 验证API密钥
```python
POST /api/v1/auth/validate

请求体:
{
    "api_key": "sk_1234567890abcdef"
}

响应:
{
    "valid": true,
    "user_id": "user123",
    "permissions": ["read", "write", "delete"],
    "rate_limit": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000
    }
}
```

## 📊 监控和统计API

### 获取使用统计
```python
GET /api/v1/stats/usage

参数:
- start_date: 开始日期
- end_date: 结束日期

示例:
GET /api/v1/stats/usage?start_date=2022-01-01&end_date=2022-01-31

响应:
{
    "total_requests": 10000,
    "successful_requests": 9500,
    "failed_requests": 500,
    "avg_response_time": 0.5,
    "most_used_symbols": [
        {"symbol": "BTC/USDT", "count": 5000},
        {"symbol": "ETH/USDT", "count": 3000}
    ],
    "most_used_agents": [
        {"agent": "technical", "count": 8000},
        {"agent": "sentiment", "count": 6000}
    ]
}
```

### 获取性能指标
```python
GET /api/v1/stats/performance

响应:
{
    "cpu_usage": 45.5,
    "memory_usage": 67.2,
    "disk_usage": 23.8,
    "network_io": {
        "bytes_sent": 1000000,
        "bytes_received": 2000000
    },
    "active_connections": 150,
    "queue_length": 5
}
```

### 获取错误日志
```python
GET /api/v1/logs/errors

参数:
- limit: 限制数量 (默认: 100)
- level: 错误级别 (error, warning, info)

示例:
GET /api/v1/logs/errors?limit=50&level=error

响应:
{
    "total": 50,
    "logs": [
        {
            "timestamp": "2022-01-01T00:00:00.000Z",
            "level": "error",
            "message": "API请求失败",
            "details": "Connection timeout"
        }
    ]
}
```

## 🚨 错误处理

### 错误响应格式
```python
{
    "error": {
        "code": "INVALID_SYMBOL",
        "message": "无效的交易对符号",
        "details": "BTC/USDT 不是有效的交易对",
        "timestamp": "2022-01-01T00:00:00.000Z"
    }
}
```

### 常见错误代码
- `INVALID_SYMBOL`: 无效的交易对符号
- `INVALID_TIMEFRAME`: 无效的时间框架
- `INVALID_AGENT`: 无效的分析代理
- `API_KEY_INVALID`: API密钥无效
- `API_KEY_EXPIRED`: API密钥已过期
- `RATE_LIMIT_EXCEEDED`: 超出速率限制
- `DATA_SOURCE_ERROR`: 数据源错误
- `ANALYSIS_FAILED`: 分析失败
- `NOT_FOUND`: 资源未找到
- `INTERNAL_ERROR`: 内部服务器错误

## 🔄 速率限制

### 限制规则
- 每分钟最多60个请求
- 每小时最多1000个请求
- 每天最多10000个请求

### 响应头信息
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
```

## 📝 示例代码

### Python示例
```python
import requests
import json

class CryptoTradingAPI:
    def __init__(self, api_key, base_url="https://api.cryptotradingagents.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_symbol(self, symbol, agents=None):
        """执行综合分析"""
        if agents is None:
            agents = ["technical", "onchain", "sentiment", "defi"]
        
        url = f"{self.base_url}/analysis/comprehensive"
        data = {
            "symbol": symbol,
            "agents": agents,
            "timeframe": "1h",
            "depth": 3
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_analysis_result(self, analysis_id):
        """获取分析结果"""
        url = f"{self.base_url}/analysis/{analysis_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_price_data(self, symbol):
        """获取价格数据"""
        url = f"{self.base_url}/data/price"
        params = {"symbol": symbol}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()

# 使用示例
api = CryptoTradingAPI("your_api_key_here")

# 执行分析
result = api.analyze_symbol("BTC/USDT")
print(f"分析ID: {result['analysis_id']}")

# 获取结果
analysis_result = api.get_analysis_result(result['analysis_id'])
print(f"信号: {analysis_result['overall_signal']}")
```

### JavaScript示例
```javascript
class CryptoTradingAPI {
    constructor(apiKey, baseUrl = 'https://api.cryptotradingagents.com/v1') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async analyzeSymbol(symbol, agents = null) {
        if (!agents) {
            agents = ['technical', 'onchain', 'sentiment', 'defi'];
        }
        
        const url = `${this.baseUrl}/analysis/comprehensive`;
        const data = {
            symbol: symbol,
            agents: agents,
            timeframe: '1h',
            depth: 3
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return response.json();
    }
    
    async getAnalysisResult(analysisId) {
        const url = `${this.baseUrl}/analysis/${analysisId}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: this.headers
        });
        
        return response.json();
    }
}

// 使用示例
const api = new CryptoTradingAPI('your_api_key_here');

// 执行分析
api.analyzeSymbol('BTC/USDT')
    .then(result => {
        console.log('分析ID:', result.analysis_id);
        return api.getAnalysisResult(result.analysis_id);
    })
    .then(analysisResult => {
        console.log('信号:', analysisResult.overall_signal);
    })
    .catch(error => {
        console.error('错误:', error);
    });
```

---

## 📚 支持和反馈

如果您在使用API时遇到问题，请：

1. 查看本文档的常见问题部分
2. 检查错误代码和错误信息
3. 访问我们的开发者论坛
4. 联系技术支持：support@cryptotradingagents.com

我们致力于提供最好的API体验，您的反馈对我们非常重要！
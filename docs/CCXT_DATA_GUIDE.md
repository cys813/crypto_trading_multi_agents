# CCXT 数据获取使用指南

## 概述

本系统已集成CCXT库来获取真实的交易所交易数据，替代了原有的模拟数据生成。支持多个主流交易所，提供实时价格、K线数据、订单簿等市场数据。

## 功能特性

### 1. 支持的交易所
- **Binance** (推荐，支持测试网)
- **OKX**
- **Huobi**
- **Coinbase**

### 2. 数据类型
- **行情数据**: 实时价格、24小时涨跌、成交量
- **K线数据**: OHLCV数据，支持多种时间框架
- **订单簿数据**: 买卖盘深度数据
- **交易数据**: 最近成交记录
- **市场深度分析**: 买卖压力、价差分析
- **聚合价格**: 多交易所加权平均价格

### 3. 技术指标计算
- **RSI**: 相对强弱指数
- **MACD**: 移动平均收敛发散
- **布林带**: Bollinger Bands
- **随机指标**: Stochastic Oscillator
- **威廉指标**: Williams %R

## 快速开始

### 1. 安装依赖

```bash
pip install ccxt numpy pandas
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入API密钥
# 或直接设置环境变量
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
```

### 3. 基本使用

```python
from crypto_trading_agents.utils.exchange_setup import initialize_exchanges
from crypto_trading_agents.data_sources.exchange_data_sources import exchange_manager

# 初始化交易所
initialize_exchanges()

# 获取行情数据
ticker = exchange_manager.get_ticker('BTC/USDT', 'binance')
print(f"当前价格: {ticker['price']}")

# 获取K线数据
ohlcv = exchange_manager.get_ohlcv('BTC/USDT', '1h', 100)
print(f"获取到 {len(ohlcv)} 条K线数据")

# 获取订单簿
order_book = exchange_manager.get_order_book('BTC/USDT', 10)
print(f"买单数量: {len(order_book['bids'])}")
print(f"卖单数量: {len(order_book['asks'])}")
```

## 详细使用说明

### 交易所设置

#### 自动初始化
```python
from crypto_trading_agents.utils.exchange_setup import initialize_exchanges

# 自动设置所有交易所
results = initialize_exchanges()
print(f"成功设置 {len(results['success'])} 个交易所")
```

#### 手动设置
```python
from crypto_trading_agents.data_sources.exchange_data_sources import (
    BinanceDataSource, exchange_manager
)

# 设置Binance交易所
binance = BinanceDataSource(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True  # 使用测试网
)
exchange_manager.register_exchange('binance', binance)
```

### 数据获取方法

#### 1. 行情数据
```python
# 获取单个交易所行情
ticker = exchange_manager.get_ticker('BTC/USDT', 'binance')

# 获取聚合价格（多交易所）
aggregated = exchange_manager.get_aggregated_price('BTC/USDT')
```

#### 2. K线数据
```python
# 获取K线数据
ohlcv = exchange_manager.get_ohlcv(
    symbol='BTC/USDT',
    timeframe='1h',    # 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
    limit=100,        # 获取100条数据
    exchange='binance'
)

# 数据格式
for candle in ohlcv:
    print(f"时间: {candle['datetime']}")
    print(f"开: {candle['open']}, 高: {candle['high']}")
    print(f"低: {candle['low']}, 收: {candle['close']}")
    print(f"成交量: {candle['volume']}")
```

#### 3. 订单簿数据
```python
# 获取订单簿
order_book = exchange_manager.get_order_book('BTC/USDT', limit=20)

# 访问买单和卖单
bids = order_book['bids']  # [[价格, 数量], ...]
asks = order_book['asks']  # [[价格, 数量], ...]

# 市场深度分析
depth = exchange_manager.get_market_depth('BTC/USDT')
print(f"买压: {depth['bid_pressure']}")
print(f"卖压: {depth['ask_pressure']}")
print(f"价差: {depth['spread']}")
```

#### 4. 技术分析师集成
```python
from crypto_trading_agents.agents.analysts.technical_analyst import TechnicalAnalyst

# 创建技术分析师
config = {
    'analysis_config': {
        'technical_indicators': ['rsi', 'macd', 'bollinger_bands']
    }
}
analyst = TechnicalAnalyst(config)

# 收集数据（自动使用CCXT获取真实数据）
data = analyst.collect_data('BTC/USDT', '2024-01-01')

# 分析数据
analysis = analyst.analyze(data)
print(f"趋势强度: {analysis['trend_strength']}")
print(f"市场状态: {analysis['market_regime']}")
```

## 高级功能

### 1. 缓存机制
```python
# 系统自动缓存数据，提高性能
# 缓存时间：行情数据60秒，K线数据5分钟

# 手动清除缓存
exchange_manager.cache.clear()

# 查看缓存状态
print(f"缓存项目数: {len(exchange_manager.cache)}")
```

### 2. 错误处理和重试
```python
# 系统自动处理网络错误和重试
# 支持多交易所降级

try:
    ticker = exchange_manager.get_ticker('BTC/USDT', 'binance')
except Exception as e:
    print(f"获取数据失败: {e}")
    # 自动尝试其他交易所
    ticker = exchange_manager.get_ticker('BTC/USDT', 'okx')
```

### 3. 速率限制
```python
# 系统自动遵守各交易所的速率限制
# Binance: 50ms间隔
# OKX: 50ms间隔
# Huobi: 100ms间隔
# Coinbase: 100ms间隔
```

## 测试和验证

### 运行测试脚本
```bash
# 在项目根目录运行
python test_ccxt_data.py
```

### 测试输出示例
```
正在初始化交易所数据源...
✓ Binance交易所设置成功（只读模式）

设置结果: 1 成功, 0 失败

测试交易所连接...
✓ binance 连接成功
  当前价格: 43250.50
  24小时成交量: 1250000000.00

=== 测试行情数据获取 ===
获取 BTC/USDT 行情数据...
  ✓ binance:
    价格: 43250.50
    24h最高: 44100.00
    24h最低: 42800.00
    24h成交量: 1250000000.00
```

## 配置说明

### API密钥设置

#### Binance (推荐)
1. 访问 https://binance.com
2. 创建API密钥
3. 设置权限：只读
4. 设置IP白名单（可选）

#### OKX
1. 访问 https://okx.com
2. 创建API密钥
3. 设置权限：只读
4. 需要设置Passphrase

#### 测试网 vs 主网
```python
# 测试网（推荐用于开发）
binance = BinanceDataSource(
    api_key="test_key",
    api_secret="test_secret",
    testnet=True
)

# 主网（用于生产）
binance = BinanceDataSource(
    api_key="prod_key",
    api_secret="prod_secret",
    testnet=False
)
```

## 故障排除

### 常见问题

#### 1. 连接失败
```bash
# 检查网络连接
ping api.binance.com

# 检查API密钥是否正确
# 检查是否设置了IP白名单
```

#### 2. 数据获取失败
```python
# 检查交易对格式是否正确
# 支持的格式: 'BTC/USDT', 'ETH/BTC', 'BNB/USDT'

# 检查时间框架是否支持
# 支持的框架: '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M'
```

#### 3. 速率限制错误
```python
# 系统自动处理速率限制
# 如遇到限制，请等待几秒后重试
```

### 调试方法

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或设置环境变量
export LOG_LEVEL=DEBUG
```

#### 检查交易所状态
```python
from crypto_trading_agents.utils.exchange_setup import exchange_setup

status = exchange_setup.get_exchange_status()
for name, info in status.items():
    print(f"{name}: {info['status']}")
```

## 性能优化

### 1. 数据缓存
- 行情数据缓存60秒
- K线数据缓存5分钟
- 自动清理过期缓存

### 2. 批量获取
```python
# 批量获取多个交易对数据
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
for symbol in symbols:
    ticker = exchange_manager.get_ticker(symbol)
```

### 3. 异步获取
```python
# 系统内部使用同步方式
# 如需异步获取，请使用asyncio + ccxt.async_support
```

## 安全建议

1. **API密钥安全**
   - 不要在代码中硬编码API密钥
   - 使用环境变量或配置文件
   - 设置适当的权限（只读）

2. **网络安全**
   - 使用HTTPS连接
   - 考虑设置IP白名单
   - 定期更换API密钥

3. **测试环境**
   - 先在测试网中测试
   - 验证数据准确性
   - 测试错误处理机制

## 扩展开发

### 添加新交易所
```python
from crypto_trading_agents.data_sources.exchange_data_sources import ExchangeDataSource

class NewExchangeDataSource(ExchangeDataSource):
    def __init__(self, api_key=None, api_secret=None):
        super().__init__(api_key, api_secret)
        self.exchange = ccxt.newexchange({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        self.rate_limit_delay = 0.1

# 注册新交易所
exchange_manager.register_exchange('newexchange', NewExchangeDataSource())
```

### 添加新数据类型
```python
def get_custom_data(self, symbol):
    # 实现自定义数据获取逻辑
    pass
```

## 总结

本系统通过CCXT库提供了强大的交易所数据获取能力，支持多交易所、多数据类型，具有良好的错误处理和缓存机制。技术分析师已完全集成真实数据获取功能，可以基于真实市场数据进行分析和决策。
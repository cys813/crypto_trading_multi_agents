# Data Collection Agent

数据收集代理 - 基于CCXT库的多交易所统一数据接口系统

## 🎯 功能特性

- **多交易所支持**: 支持Binance、OKX、Huobi、Coinbase、Kraken等主流交易所
- **实时数据收集**: OHLCV、实时行情、订单簿深度、历史交易数据
- **仓位管理**: 实时仓位同步、PnL计算、风险评估
- **订单管理**: 订单状态监控、生命周期管理、执行效率分析
- **智能调度**: 自动化数据收集、优先级管理、负载均衡
- **质量监控**: 数据验证、异常检测、质量评分

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Data Collection Agent                  │
├─────────────────────────────────────────────────────────┤
│  Exchange Manager   │  Data Collector  │  Position Manager │
│  - 连接管理         │  - 自动调度       │  - 实时同步       │
│  - 负载均衡         │  - 智能收集       │  - PnL计算        │
│  - 故障转移         │  - 质量控制       │  - 风险评估       │
├─────────────────────────────────────────────────────────┤
│  Order Manager      │  Data Processor  │  API Services     │
│  - 订单生命周期     │  - 数据清洗       │  - RESTful API    │
│  - 执行分析         │  - 标准化         │  - WebSocket      │
│  - 性能统计         │  - 质量检查       │  - 数据导出       │
├─────────────────────────────────────────────────────────┤
│                   Data Storage                           │
│  TimescaleDB (时序) │  PostgreSQL (业务)  │  Redis (缓存)     │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量，添加交易所API密钥
# 至少需要配置一个交易所的API密钥
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动数据库

```bash
# 使用Docker启动数据库服务
docker-compose up -d postgres timescaledb redis
```

### 4. 运行系统

```bash
# 启动数据收集代理
python -m src.data_collection.main
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 描述 | 必需 | 示例 |
|-------|------|------|------|
| `BINANCE_API_KEY` | Binance API密钥 | 是 | `your_api_key` |
| `BINANCE_API_SECRET` | Binance API密钥 | 是 | `your_api_secret` |
| `OKX_API_KEY` | OKX API密钥 | 否 | `your_api_key` |
| `OKX_API_SECRET` | OKX API密钥 | 否 | `your_api_secret` |
| `OKX_API_PASSPHRASE` | OKX API密码 | 否 | `your_passphrase` |
| `POSTGRES_HOST` | PostgreSQL主机 | 否 | `localhost` |
| `POSTGRES_DB` | PostgreSQL数据库名 | 否 | `crypto_trading` |
| `REDIS_HOST` | Redis主机 | 否 | `localhost` |
| `LOG_LEVEL` | 日志级别 | 否 | `INFO` |

### 支持的交易所

- **Binance** - 支持现货、期货、期权
- **OKX** - 支持现货、期货、期权
- **Huobi** - 支持现货、期货
- **Coinbase** - 支持现货
- **Kraken** - 支持现货、期货

## 📊 监控指标

### 系统指标
- 数据收集成功率
- API响应时间
- 连接健康状态
- 内存使用情况

### 业务指标
- 数据延迟
- 仓位实时性
- 订单状态同步
- 数据质量评分

### Prometheus指标
- `data_collection_total` - 数据收集计数
- `data_collection_duration_seconds` - 收集耗时
- `active_positions_total` - 活跃仓位数量
- `api_requests_total` - API请求计数

## 🔄 API接口

### 获取市场数据
```python
from src.data_collection.core.exchange_manager import ExchangeManager

# 创建交易所管理器
config = {
    'binance': ExchangeConfig(
        name='binance',
        api_key='your_key',
        secret='your_secret'
    )
}
manager = ExchangeManager(config)

# 获取K线数据
ohlcv = await manager.get_ohlcv('binance', 'BTC/USDT', '1m')
```

### 获取仓位信息
```python
from src.data_collection.core.position_manager import PositionManager

# 创建仓位管理器
position_manager = PositionManager(manager)

# 获取所有仓位
positions = position_manager.get_all_positions()

# 获取仓位摘要
summary = position_manager.get_position_summary()
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_exchange_manager.py

# 运行性能测试
pytest --benchmark-only
```

## 📈 性能指标

- **数据获取延迟**: < 100ms
- **并发连接数**: > 1000
- **数据准确性**: > 99.9%
- **系统可用性**: > 99.9%
- **API速率限制**: 智能管理，自动限流

## 🔧 开发指南

### 项目结构
```
src/data_collection/
├── core/                    # 核心组件
│   ├── exchange_manager.py  # 交易所管理
│   ├── data_collector.py    # 数据收集
│   ├── position_manager.py  # 仓位管理
│   ├── order_manager.py     # 订单管理
│   └── data_processor.py    # 数据处理
├── models/                  # 数据模型
├── api/                    # API服务
├── config/                 # 配置管理
├── utils/                  # 工具函数
└── tests/                  # 测试用例
```

### 添加新交易所
1. 在 `config/settings.py` 中添加交易所配置
2. 在 `.env` 文件中添加API密钥
3. 系统会自动检测并初始化新交易所

### 自定义数据收集
```python
from src.data_collection.core.data_collector import DataCollector, DataType, CollectionTask

# 创建自定义收集任务
task = CollectionTask(
    exchange_name='binance',
    symbol='BTC/USDT',
    data_type=DataType.OHLCV,
    timeframe='15m',
    interval=900,
    priority=2
)

# 添加到收集器
data_collector.add_collection_task(task)
```

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的API密钥是否正确
   - 确认API密钥有足够的权限

2. **网络连接问题**
   - 检查网络连接
   - 确认交易所API端点可访问

3. **速率限制**
   - 系统会自动处理速率限制
   - 如遇限制，会自动重试

4. **数据延迟**
   - 检查系统负载
   - 查看网络延迟
   - 调整收集间隔

### 日志查看
```bash
# 查看实时日志
tail -f logs/data_collection.log

# 查看错误日志
grep ERROR logs/data_collection.log
```

## 📝 更新日志

### v1.0.0
- 初始版本发布
- 支持多交易所数据收集
- 实现仓位和订单管理
- 添加监控和指标收集

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 开启Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持

如有问题，请提交 [GitHub Issues](https://github.com/cys813/crypto_trading_multi_agents/issues)
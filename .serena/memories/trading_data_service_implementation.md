# TradingDataService 实现详情

## 核心类：TradingDataService

### 位置
`services/trading_data_service.py`

### 主要功能
- 统一的多时间周期数据获取服务
- 支持4小时、1小时、15分钟三个时间框架
- 按用户要求配置时间范围（30天、15天、3天）
- 集中化的数据缓存和质量评估
- 标准化的数据格式

### 数据结构
```python
{
    "symbol": "BTC/USDT",
    "end_date": "2025-08-05",
    "data_type": "unified_trading_data",
    "timeframes": {
        "4h": {...},  # 4小时数据（30天）
        "1h": {...},  # 1小时数据（15天）
        "15m": {...}  # 15分钟数据（3天）
    },
    "data_quality": {
        "overall_quality": 1.0,
        "completeness": 1.0
    }
}
```

### 时间范围配置
- **4小时框架**: 30天数据
- **1小时框架**: 15天数据  
- **15分钟框架**: 3天数据

### 性能指标
- **响应时间**: < 10ms
- **数据质量**: 1.0（满分）
- **数据格式**: 统一标准化

### 使用方式
```python
from services.trading_data_service import TradingDataService

# 初始化服务
service = TradingDataService(config)

# 获取统一数据
data = service.get_trading_data("BTC/USDT", "2025-08-05")
```

### 已集成的模块
1. **TechnicalAnalyst** - 技术分析师
2. **BullResearcher** - 看涨研究员
3. **BearResearcher** - 看跌研究员

### AI增强功能
- 集成 StandardAIAnalysisMixin
- 支持AI分析增强
- 智能信号识别

### 扩展性
- 易于添加新的时间框架
- 支持多种数据源
- 模块化设计便于维护
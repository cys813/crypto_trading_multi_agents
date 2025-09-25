# 数据收集代理 (Data Collection Agent)

## 概述

数据收集代理是一个基于CCXT库的多交易所统一数据接口系统，提供全面的加密货币交易数据收集、处理和存储功能。该系统支持实时市场数据获取、仓位信息管理、挂单信息监控，以及高质量的数据处理和质量控制。

## 核心功能

### 1. 市场数据收集
- **K线数据获取**: 支持多时间框架（1m, 5m, 15m, 30m, 1h, 4h, 1d）
- **实时行情数据**: 获取最新价格、买卖盘口信息
- **订单簿深度数据**: 支持可配置深度的订单簿数据
- **历史交易数据**: 获取历史成交记录
- **增量数据获取**: 智能的数据同步机制

### 2. 仓位信息管理
- **实时仓位数据**: 从交易所同步当前仓位
- **盈亏计算**: 实时计算未实现盈亏和已实现盈亏
- **风险评估**: 提供仓位风险指标和预警
- **仓位变更历史**: 记录仓位的完整变更轨迹

### 3. 挂单信息管理
- **实时挂单数据**: 监控所有挂单状态
- **订单状态跟踪**: 完整的订单生命周期管理
- **执行分析**: 订单执行效率和质量分析
- **订单统计**: 提供全面的订单执行统计

### 4. 数据处理和质量控制
- **数据清洗**: 自动检测和处理异常数据
- **数据验证**: 多层数据质量检查机制
- **异常数据处理**: 智能的异常数据识别和修复
- **数据标准化**: 跨交易所数据格式统一

## 技术架构

### 数据库架构
- **TimescaleDB**: 时序数据存储（市场数据）
- **PostgreSQL**: 业务数据存储（仓位、订单）
- **Redis**: 高速缓存和会话存储

### 技术栈
- **后端框架**: Python 3.8+ + AsyncIO + FastAPI
- **数据库ORM**: SQLAlchemy
- **交易所接口**: CCXT 4.0+
- **异步处理**: asyncio + aiofiles
- **数据验证**: Pydantic + 自定义验证器
- **监控指标**: Prometheus + Grafana

### 核心组件

#### Exchange Manager（交易所管理器）
- CCXT库集成和统一接口
- 多交易所连接管理
- 连接池和负载均衡
- API速率限制和故障转移

#### Data Collector（数据收集器）
- 自动化数据收集调度
- 多种数据类型支持
- 智能重试机制
- 数据质量实时监控

#### Position Manager（仓位管理器）
- 实时仓位同步
- PnL计算和分析
- 风险指标监控
- 仓位历史记录

#### Order Manager（订单管理器）
- 订单状态实时跟踪
- 执行效率分析
- 订单生命周期管理
- 性能统计报表

#### Data Processor（数据处理器）
- 数据清洗和标准化
- 异常检测和修复
- 数据质量评估
- 统计分析功能

## 安装和部署

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- TimescaleDB 2.0+
- Redis 6.0+
- Docker (可选)

### 本地安装

1. **克隆项目**
```bash
git clone <repository-url>
cd crypto_trading_multi_agents
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和交易所API密钥
```

4. **初始化数据库**
```bash
python -c "
from src.data_collection.models.database import create_tables
create_tables()
"
```

5. **启动服务**
```bash
# 开发模式
python -m src.data_collection.main

# 生产模式
uvicorn src.data_collection.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker部署

1. **使用Docker Compose**
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f data-collection
```

2. **单独构建Docker镜像**
```bash
docker build -t data-collection-agent .

# 运行容器
docker run -d -p 8000:8000 --name data-collection data-collection-agent
```

## API文档

### 启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 主要API端点

#### 市场数据接口
- `GET /api/v1/market/exchanges` - 获取支持的交易所列表
- `GET /api/v1/market/exchanges/{exchange}/symbols` - 获取交易所交易对
- `POST /api/v1/market/ohlcv` - 获取K线数据
- `POST /api/v1/market/orderbook` - 获取订单簿数据
- `POST /api/v1/market/trades` - 获取交易数据
- `POST /api/v1/market/ticker` - 获取行情数据

#### 仓位管理接口
- `GET /api/v1/positions/` - 获取所有仓位
- `GET /api/v1/positions/{position_id}` - 获取特定仓位
- `GET /api/v1/positions/summary` - 获取仓位汇总
- `GET /api/v1/positions/risk` - 获取风险指标

#### 订单管理接口
- `GET /api/v1/orders/` - 获取所有订单
- `GET /api/v1/orders/{order_id}` - 获取特定订单
- `GET /api/v1/orders/summary` - 获取订单汇总
- `GET /api/v1/orders/performance` - 获取执行性能

#### 系统接口
- `GET /health` - 健康检查
- `GET /api/v1/system/info` - 系统信息
- `GET /api/v1/system/metrics` - 系统指标

## 配置说明

### 环境变量配置

```bash
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=crypto_trading

# TimescaleDB配置
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=password
TIMESCALEDB_DB=timescaledb_crypto

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 交易所API配置
BINANCE_API_KEY=your_api_key
BINANCE_SECRET=your_secret
OKX_API_KEY=your_api_key
OKX_SECRET=your_secret
OKX_PASSPHRASE=your_passphrase

# 性能配置
MAX_CONCURRENT_CONNECTIONS=1000
DATA_COLLECTION_INTERVAL=1000
DATA_QUALITY_THRESHOLD=0.999
```

### 支持的交易所
- Binance (币安)
- OKX (欧易)
- Huobi (火币)
- 可通过CCXT扩展支持更多交易所

## 监控和指标

### 系统监控
- **Prometheus**: 指标收集和存储
- **Grafana**: 可视化仪表板
- **健康检查**: 自动系统健康监控
- **日志记录**: 结构化日志输出

### 关键指标
- 数据收集延迟 (< 100ms)
- 数据准确率 (> 99.9%)
- 系统可用性 (> 99.9%)
- API响应时间
- 数据质量分数

### Grafana仪表板
访问 http://localhost:3000 查看预配置的监控仪表板

## 测试

### 运行测试
```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest src/data_collection/tests/

# 运行特定测试文件
pytest src/data_collection/tests/test_exchange_manager.py

# 生成覆盖率报告
pytest --cov=src.data_collection --cov-report=html
```

### 测试覆盖范围
- 单元测试：核心组件功能测试
- 集成测试：组件间交互测试
- API测试：REST接口功能测试
- 性能测试：系统负载测试

## 性能优化

### 数据库优化
- TimescaleDB超表分区
- 索引优化策略
- 查询性能调优
- 连接池管理

### 缓存策略
- Redis缓存热点数据
- 查询结果缓存
- API响应缓存
- 内存缓存优化

### 并发处理
- 异步I/O操作
- 连接池管理
- 任务队列优化
- 资源限制控制

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker-compose ps postgres
   docker-compose logs postgres
   ```

2. **交易所API连接问题**
   ```bash
   # 检查API密钥配置
   # 验证网络连接
   # 查看详细错误日志
   docker-compose logs data-collection
   ```

3. **数据收集异常**
   ```bash
   # 检查数据收集状态
   curl http://localhost:8000/api/v1/market/collection/status

   # 查看系统指标
   curl http://localhost:8000/api/v1/system/metrics
   ```

### 日志分析
```bash
# 查看实时日志
docker-compose logs -f data-collection

# 过滤特定级别的日志
docker-compose logs data-collection | grep ERROR

# 查看特定组件日志
docker-compose logs data-collection | grep "ExchangeManager"
```

## 扩展开发

### 添加新交易所
1. 在配置文件中添加交易所配置
2. 实现交易所特定的数据格式转换
3. 添加相应的数据验证规则
4. 更新测试用例

### 自定义数据处理
1. 继承基础数据处理器类
2. 实现自定义处理逻辑
3. 注册到数据收集流程
4. 添加相应的验证和测试

### 扩展API接口
1. 在对应的API路由文件中添加新端点
2. 实现请求和响应模型
3. 添加必要的业务逻辑
4. 编写API测试

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码变更
4. 确保通过所有测试
5. 提交Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 支持

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至开发团队
- 查看项目文档和Wiki

---

**注意**: 这是一个生产级的数据收集系统，请确保在生产环境使用前进行充分的测试和配置调优。
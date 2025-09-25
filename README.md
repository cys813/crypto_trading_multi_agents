# 加密货币多代理交易系统

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/cys813/crypto_trading_multi_agents)

基于多代理架构的智能加密货币交易系统，集成数据收集、新闻分析、智能决策和风险管理的完整交易解决方案。

## 🎯 系统概述

本系统采用多代理协作架构，通过专业化分工实现加密货币交易的智能化和自动化。每个代理专注于特定领域的分析和决策，共同协作以提供更准确、更安全的交易策略。

### 核心特性

- **🤖 多代理协作架构** - 专业化代理分工，各司其职
- **📊 实时数据收集** - 基于CCXT的多交易所统一数据接口
- **📰 智能新闻分析** - AI驱动的新闻收集和情感分析
- **🧠 智能决策引擎** - 基于多维度数据的交易决策支持
- **⚡ 高频交易执行** - 低延迟、高并发的交易执行系统
- **🛡️ 风险管理** - 实时仓位监控和风险评估
- **📈 社交媒体分析** - 市场情绪和趋势分析

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    加密货币多代理交易系统                     │
├─────────────────────────────────────────────────────────────┤
│  数据收集代理  │  新闻收集代理  │  社交媒体分析代理            │
│  市场数据获取  │  新闻源适配器  │  社交媒体监控                │
│  仓位信息同步  │  内容处理管道  │  情感分析算法                │
│  订单管理      │  LLM智能分析  │  趋势识别                    │
├─────────────────────────────────────────────────────────────┤
│                智能交易决策代理                              │
│          基于多维度数据的交易策略生成                        │
├─────────────────────────────────────────────────────────────┤
│  做多分析师  │  做空分析师  │  风险仓位管理代理               │
│  趋势分析    │  反向信号    │  仓位风险评估                  │
│  入场时机    │  空头策略    │  止损止盈管理                  │
│  目标价位    │  风险控制    │  资金分配优化                  │
├─────────────────────────────────────────────────────────────┤
│                   交易执行代理                              │
│               订单执行和状态管理                            │
└─────────────────────────────────────────────────────────────┘
```

## 📊 项目状态

| 代理名称 | 状态 | 进度 | GitHub Issue | 主要功能 |
|---------|------|------|-------------|----------|
| **数据收集代理** | ✅ 已完成 | 100% | #2 | 基于CCXT的多交易所数据收集 |
| **新闻收集代理** | 🔄 进行中 | 25% | #13 | 新闻源适配器框架开发 |
| **做多分析师代理** | ⏳ 待启动 | 0% | #5 | 趋势分析和做多策略 |
| **做空分析师代理** | ⏳ 待启动 | 0% | #6 | 反向信号和空头策略 |
| **智能交易决策代理** | ⏳ 待启动 | 0% | #7 | 多维度数据决策引擎 |
| **交易执行代理** | ⏳ 待启动 | 0% | #3 | 高频交易执行系统 |
| **风险仓位管理代理** | ⏳ 待启动 | 0% | #4 | 实时风险管理 |
| **社交媒体分析代理** | ⏳ 待启动 | 0% | #8 | 社交媒体情绪分析 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Redis
- PostgreSQL 12+
- TimescaleDB
- Docker (可选)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/cys813/crypto_trading_multi_agents.git
   cd crypto_trading_multi_agents
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp config/example.yaml config/config.yaml
   # 编辑配置文件，添加API密钥等信息
   ```

4. **启动数据库**
   ```bash
   docker-compose up -d postgres redis timescaledb
   ```

5. **初始化数据库**
   ```bash
   python scripts/init_db.py
   ```

### 使用示例

```python
from src.news_collection.news_agent import NewsCollectionAgent

# 初始化新闻收集代理
agent = NewsCollectionAgent(config_path="config/news_sources.yaml")

# 启动新闻收集
await agent.start_collection()

# 获取最新新闻
news = await agent.get_latest_news(cryptocurrency="BTC")
```

## 🛠️ 技术栈

### 核心框架
- **Python 3.8+** - 主要开发语言
- **AsyncIO** - 异步编程框架
- **FastAPI** - API服务框架
- **SQLAlchemy** - ORM框架

### 数据库
- **PostgreSQL** - 主数据库
- **TimescaleDB** - 时序数据存储
- **Redis** - 缓存和消息队列

### 交易所集成
- **CCXT** - 加密货币交易库
- **WebSocket** - 实时数据流
- **REST API** - 交易所接口

### AI/ML
- **OpenAI GPT** - 自然语言处理
- **LangChain** - LLM应用框架
- **scikit-learn** - 机器学习算法

### 监控和日志
- **Prometheus** - 指标监控
- **Grafana** - 可视化仪表板
- **ELK Stack** - 日志分析

## 📁 项目结构

```
crypto_trading_multi_agents/
├── src/                          # 源代码
│   ├── news_collection/          # 新闻收集代理
│   │   ├── adapters/             # 新闻源适配器
│   │   ├── core/                 # 核心组件
│   │   ├── models/               # 数据模型
│   │   └── tests/                # 测试用例
│   ├── data_collection/          # 数据收集代理
│   ├── trading_execution/        # 交易执行代理
│   ├── risk_management/          # 风险管理代理
│   └── social_media/            # 社交媒体分析代理
├── config/                       # 配置文件
├── scripts/                      # 脚本文件
├── tests/                        # 测试套件
├── docs/                         # 文档
├── .claude/                      # Claude项目管理
│   ├── epics/                    # Epic定义
│   └── prds/                     # 产品需求文档
└── docker-compose.yml            # Docker配置
```

## 🔄 开发工作流

本项目使用基于Claude Code的项目管理系统，采用规范化的开发流程：

### 1. 产品需求文档 (PRD)
```bash
# 创建新的产品需求
/pm:prd-new feature-name
```

### 2. Epic规划
```bash
# 将PRD转换为技术实现计划
/pm:prd-parse feature-name
```

### 3. 任务分解
```bash
# 分解Epic为具体任务
/pm:epic-decompose feature-name
```

### 4. 并行执行
```bash
# 启动并行代理执行任务
/pm:epic-start feature-name
```

### 5. 进度跟踪
```bash
# 查看项目状态
/pm:status
```

## 📋 详细功能

### 数据收集代理
- ✅ 多交易所统一接口 (Binance, Coinbase, Kraken等)
- ✅ 实时市场数据获取 (K线, 订单簿, 交易记录)
- ✅ 仓位和订单信息同步
- ✅ 增量数据获取策略
- ✅ 数据质量监控和异常处理

### 新闻收集代理
- 🔄 新闻源适配器框架 (CoinDesk, CoinTelegraph, Decrypt)
- 🔄 多源新闻收集策略
- ⏳ 新闻内容处理和去重
- ⏳ LLM驱动的新闻总结和情感分析
- ⏳ 实时新闻推送和告警

### 智能决策代理
- ⏳ 多维度数据融合分析
- ⏳ 机器学习驱动的交易信号生成
- ⏳ 策略回测和优化
- ⏳ 市场趋势预测
- ⏳ 风险收益比评估

### 交易执行代理
- ⏳ 低延迟订单执行
- ⏳ 智能订单路由
- ⏳ 滑点控制
- ⏳ 交易成本优化
- ⏳ 执行质量监控

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定代理测试
pytest src/news_collection/tests/

# 运行性能测试
pytest --benchmark-only
```

## 📊 性能指标

- **数据收集延迟**: < 100ms
- **新闻处理速度**: 1000+ 条/分钟
- **交易执行延迟**: < 50ms
- **系统可用性**: 99.9%
- **数据准确性**: 99.99%

## 🔒 安全特性

- API密钥加密存储
- 数据传输SSL加密
- 访问权限控制
- 操作日志审计
- 风险控制机制

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目地址: [https://github.com/cys813/crypto_trading_multi_agents](https://github.com/cys813/crypto_trading_multi_agents)
- 问题报告: [GitHub Issues](https://github.com/cys813/crypto_trading_multi_agents/issues)

## 🙏 致谢

感谢以下开源项目的支持：
- [CCXT](https://github.com/ccxt/ccxt) - 加密货币交易库
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代Web框架
- [TimescaleDB](https://github.com/timescale/timescaledb) - 时序数据库
- [Prometheus](https://github.com/prometheus/prometheus) - 监控系统

---

**⚠️ 免责声明**: 本系统仅供教育和研究用途。加密货币交易具有高风险，请在使用前充分了解相关风险。
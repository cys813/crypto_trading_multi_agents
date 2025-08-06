# 加密货币交易智能代理系统

## 🚀 项目概述

Crypto Trading Agents 是一个基于多智能代理架构的加密货币交易分析系统，集成了技术分析、链上分析、情绪分析、DeFi分析和做市商分析等多个专业领域的AI代理。

## 🎯 主要特性

### 🤖 多智能代理架构
- **技术分析师**: 专业的图表模式识别和技术指标分析
- **链上分析师**: 区块链数据分析和巨鲸活动追踪
- **情绪分析师**: 市场情绪和社交媒体趋势分析
- **DeFi分析师**: 去中心化金融协议分析
- **做市商分析师**: 订单簿和流动性深度分析

### 🌐 现代化Web界面
- 响应式设计，支持多设备访问
- 实时进度跟踪和状态更新
- 直观的用户界面和交互体验
- 专业的加密货币主题设计

### 📊 数据源集成
- **市场数据**: CoinGecko、CoinMarketCap
- **链上数据**: Glassnode、IntoTheBlock
- **DeFi数据**: DeFiLlama、DeFi Pulse
- **情绪数据**: LunarCrush、Santiment
- **交易所数据**: Binance、Coinbase、OKX、Huobi

### 🔧 智能配置管理
- 环境变量配置
- 用户偏好设置持久化
- 会话状态管理
- 分析模板管理

## 📁 项目结构

```
crypto_trading_agents/
├── crypto_trading_agents/          # 主要代码目录
│   ├── agents/                     # 代理实现
│   │   ├── analysts/              # 分析师代理
│   │   ├── managers/              # 管理器代理
│   │   ├── researchers/           # 研究员代理
│   │   ├── risk_managers/         # 风险管理代理
│   │   └── traders/               # 交易员代理
│   ├── config/                    # 配置文件
│   ├── src/
│   │   ├── data_sources/          # 数据源实现
│   │   └── database/              # 数据库模型和工具
│   ├── llm/                       # 大语言模型适配器
│   ├── tools/                     # 工具函数
│   ├── web/                       # Web界面
│   │   ├── components/            # 组件
│   │   └── utils/                 # 工具函数
│   └── utils/                     # 通用工具
├── data/                          # 数据目录
├── docs/                          # 文档目录
├── examples/                      # 示例代码
├── scripts/                       # 脚本文件
└── tests/                         # 测试文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器
- 互联网连接（用于API调用）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd crypto_trading_agents
```

2. **安装依赖**
```bash
pip install -r requirements.txt
pip install -r requirements_web.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入您的API密钥
```

4. **启动Web界面**
```bash
python start_web.py
```

5. **访问应用**
打开浏览器访问 `http://localhost:8501`

## 🔧 配置说明

### 环境变量配置

系统支持以下配置类别：

#### LLM提供商配置
```env
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic配置
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI配置
GOOGLE_API_KEY=your_google_api_key_here
```

#### 加密货币交易所配置
```env
# Binance配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Coinbase配置
COINBASE_API_KEY=your_coinbase_api_key_here
COINBASE_API_SECRET=your_coinbase_api_secret_here
COINBASE_PASSPHRASE=your_coinbase_passphrase_here
```

#### 数据源配置
```env
# CoinGecko配置
COINGECKO_API_KEY=your_coingecko_api_key_here
COINGECKO_DEMO_MODE=true

# Glassnode配置
GLASSNODE_API_KEY=your_glassnode_api_key_here

# LunarCrush配置
LUNARCRUSH_API_KEY=your_lunarcrush_api_key_here
```

### 分析配置

```env
# 分析深度
DEFAULT_ANALYSIS_DEPTH=3

# 启用的分析类型
ENABLE_TECHNICAL_ANALYSIS=true
ENABLE_ONCHAIN_ANALYSIS=true
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_DEFI_ANALYSIS=true
ENABLE_MARKET_MAKER_ANALYSIS=true

# 技术指标
TECHNICAL_INDICATORS=rsi,macd,bollinger_bands,ichimoku,stochastic,williams_r

# 时间框架
TIMEFRAMES=1m,5m,15m,1h,4h,1d,1w
```

## 🎮 使用指南

### Web界面使用

1. **选择交易对**
   - 从下拉菜单选择要分析的加密货币交易对
   - 系统支持主流交易对（BTC/USDT、ETH/USDT等）

2. **配置分析代理**
   - 选择要启用的分析代理
   - 每个代理专注于不同的分析维度

3. **设置分析参数**
   - 调整分析深度
   - 选择时间框架
   - 配置风险参数

4. **执行分析**
   - 点击"开始分析"按钮
   - 实时查看分析进度
   - 等待分析结果

5. **查看结果**
   - 查看综合分析报告
   - 导出分析结果（JSON、Markdown）
   - 保存分析历史

### 代理功能说明

#### 技术分析师
- **功能**: 识别图表模式、计算技术指标
- **指标**: RSI、MACD、布林带、一目均衡表等
- **输出**: 技术面分析报告、买卖信号

#### 链上分析师
- **功能**: 分析区块链数据、追踪巨鲸活动
- **数据**: 地址活跃度、交易量、持币分布
- **输出**: 链上健康状况、异常活动警报

#### 情绪分析师
- **功能**: 分析市场情绪、社交媒体趋势
- **数据**: 推特情绪、讨论热度、新闻情感
- **输出**: 情绪指标、市场热度分析

#### DeFi分析师
- **功能**: 分析DeFi协议、流动性池
- **数据**: TVL、收益率、协议风险
- **输出**: DeFi投资机会、风险评估

#### 做市商分析师
- **功能**: 分析订单簿、流动性深度
- **数据**: 买卖压力、价差、大单交易
- **输出**: 市场深度分析、短期价格预测

## 📊 数据源详情

### 市场数据源
- **CoinGecko**: 加密货币价格、市场数据
- **CoinMarketCap**: 实时价格、市值数据
- **演示模式**: 无需API密钥的模拟数据

### 链上数据源
- **Glassnode**: 专业的链上数据分析
- **IntoTheBlock**: 智能链上分析
- **Nansen**: 巨鲸地址追踪

### DeFi数据源
- **DeFiLlama**: DeFi协议TVL数据
- **DeFi Pulse**: DeFi项目排名
- **Uniswap**: DEX流动性数据

### 情绪数据源
- **LunarCrush**: 社交媒体情绪分析
- **Santiment**: 市场情绪指标
- **TheTIE**: 情绪评分系统

### 交易所数据源
- **Binance**: 全球最大的加密货币交易所
- **Coinbase**: 美国主流交易所
- **OKX**: 亚洲领先的交易所
- **Huobi**: 全球数字资产交易所

## 🔍 高级功能

### 自定义分析模板
- 保存常用的分析配置
- 快速应用预设参数
- 分享分析模板

### 批量分析
- 同时分析多个交易对
- 批量导出分析结果
- 对比分析报告

### 实时监控
- 设置价格警报
- 实时数据更新
- 自动重新分析

### 风险管理
- 止损设置
- 仓位管理
- 风险评估报告

## 🛠️ 开发指南

### 代码结构
```
crypto_trading_agents/
├── agents/          # 代理实现
│   ├── analysts/   # 分析师代理
│   ├── managers/   # 管理器代理
│   └── utils/      # 代理工具
├── config/         # 配置管理
├── src/
│   ├── data_sources/   # 数据源实现
│   └── database/       # 数据库模型
├── llm/           # LLM适配器
├── tools/         # 工具函数
├── web/           # Web界面
└── utils/         # 通用工具
```

### 添加新的分析代理
1. 在 `agents/analysts/` 目录下创建新的代理文件
2. 继承基础代理类
3. 实现分析方法
4. 注册到系统中

### 添加新的数据源
1. 在 `src/data_sources/` 目录下创建数据源文件
2. 继承基础数据源类
3. 实现API接口
4. 注册到数据源管理器

### 自定义Web组件
1. 在 `web/components/` 目录下创建组件文件
2. 使用Streamlit API
3. 集成到主应用中

## 🐛 故障排除

### 常见问题

#### API密钥错误
- 检查API密钥是否正确
- 确认API密钥权限
- 验证API余额

#### 网络连接问题
- 检查互联网连接
- 验证防火墙设置
- 确认API端点可访问

#### 分析失败
- 查看错误日志
- 检查数据源状态
- 验证代理配置

#### Web界面问题
- 清除浏览器缓存
- 检查端口占用
- 重启应用服务器

### 调试模式
```env
DEBUG=true
VERBOSE=true
LOG_LEVEL=DEBUG
```

## 📈 性能优化

### 缓存策略
- 启用数据缓存
- 配置缓存过期时间
- 使用内存缓存

### 并发处理
- 配置最大工作线程
- 设置请求超时
- 实现重试机制

### 数据优化
- 批量数据获取
- 数据压缩存储
- 增量数据更新

## 🔒 安全注意事项

### API密钥安全
- 不要在代码中硬编码API密钥
- 使用环境变量存储密钥
- 定期更换API密钥

### 数据安全
- 加密敏感数据
- 使用HTTPS连接
- 定期备份数据

### 访问控制
- 限制API访问频率
- 实施IP白名单
- 监控异常访问

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📞 支持与反馈

- **问题报告**: [GitHub Issues](https://github.com/your-repo/issues)
- **功能请求**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **邮件支持**: support@your-domain.com

## 📚 相关资源

- [Streamlit文档](https://docs.streamlit.io/)
- [CCXT文档](https://ccxt.readthedocs.io/)
- [加密货币API文档](https://docs.coincap.io/)
- [区块链数据分析指南](https://glassnodeacademy.com/)

---

**免责声明**: 本系统仅用于教育和研究目的，不构成投资建议。加密货币交易具有高风险，请谨慎投资。
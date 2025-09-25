# 测试目录结构

此目录包含所有测试文件，按功能分类组织。

## 目录结构

```
tests/
├── README.md                    # 本文件
├── run_tests.py                # 测试运行器
├── __init__.py                 # Python包初始化
├── ai/                         # AI相关测试
│   ├── __init__.py
│   ├── test_ai_enhanced_analysis.py
│   ├── test_ai_enhanced_modules.py
│   ├── test_ai_independent.py
│   ├── test_ai_integration_simple.py
│   ├── test_ai_simple.py
│   ├── test_defi_ai_integration.py
│   ├── test_onchain_ai_analysis.py
│   ├── test_onchain_simple.py
│   ├── test_sentiment_ai_integration.py
│   └── test_sentiment_ai_simple.py
├── analysis/                   # 分析师相关测试
│   ├── __init__.py
│   ├── test_analysts.py
│   └── test_enhanced_technical_analyst.py
├── core/                       # 核心功能测试
│   ├── __init__.py
│   ├── test_basic_functionality.py
│   ├── test_core_functionality.py
│   └── test_syntax_check.py
├── integration/                # 系统集成测试
│   ├── __init__.py
│   ├── test_complete_system.py
│   └── test_unified_llm_service.py
└── trading_data/              # 交易数据相关测试
    ├── __init__.py
    ├── test_ccxt_data.py
    ├── test_layered_data.py
    ├── test_simple_layered.py
    ├── test_simple_trading_data.py
    ├── test_trading_data_simple.py
    └── test_trading_data_system.py
```

## 测试分类

### 🤖 AI测试 (ai/)
- **AI增强分析**: AI功能集成和增强分析测试
- **情感分析**: 基于AI的市场情感分析测试
- **DeFi集成**: DeFi协议和AI分析集成测试
- **链上分析**: 区块链数据和AI分析测试

### 📊 分析师测试 (analysis/)
- **技术分析师**: 技术指标和图表分析测试
- **增强分析师**: AI增强的技术分析测试

### ⚙️ 核心功能测试 (core/)
- **基础功能**: 基本系统功能测试
- **核心服务**: 统一交易数据架构测试
- **语法检查**: 代码质量和语法测试

### 🔗 集成测试 (integration/)
- **完整系统**: 端到端系统集成测试
- **LLM服务**: 统一LLM框架集成测试

### 📈 交易数据测试 (trading_data/)
- **CCXT数据**: 交易所数据获取测试
- **分层数据**: 分层数据架构测试
- **统一数据**: 统一交易数据服务测试

## 运行测试

### 运行单个测试
```bash
# 运行核心功能测试
python crypto_trading_agents/tests/core/test_core_functionality.py

# 运行交易数据测试
python crypto_trading_agents/tests/trading_data/test_trading_data_simple.py
```

### 运行分类测试
```bash
# 运行所有核心测试
python -m pytest crypto_trading_agents/tests/core/

# 运行所有AI测试
python -m pytest crypto_trading_agents/tests/ai/
```

### 运行所有测试
```bash
# 使用测试运行器
python crypto_trading_agents/tests/run_tests.py

# 或使用pytest
python -m pytest crypto_trading_agents/tests/
```

## 测试状态

### ✅ 已验证测试
- `test_core_functionality.py` - 核心功能正常
- 统一交易数据架构测试通过

### ⚠️ 需要修复的测试
- 部分测试文件存在相对导入问题
- 一些测试需要更新配置参数

### 🔧 改进计划
1. 修复相对导入问题
2. 统一测试配置格式
3. 添加性能测试基准
4. 完善错误处理测试

## 贡献指南

### 添加新测试
1. 在适当的分类目录下创建测试文件
2. 使用 `test_` 前缀命名文件
3. 包含清晰的文档字符串
4. 添加适当的错误处理

### 测试约定
- 使用描述性的测试函数名
- 包含测试目的的文档字符串
- 提供清晰的成功/失败输出
- 处理异常情况并提供有用的错误信息

### 路径管理
测试文件应使用以下模式设置路径：
```python
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../crypto_trading_agents'))
```

这确保了测试可以正确导入项目模块。
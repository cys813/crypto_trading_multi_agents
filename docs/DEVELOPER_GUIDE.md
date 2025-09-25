# 开发者指南

## 🏗️ 架构概述

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Agent System   │    │  Data Sources   │
│   (Streamlit)   │    │   (Multi-Agent) │    │   (APIs/CCXT)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Core Engine   │
                    │  (Orchestration)│
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Data Storage  │
                    │ (JSON/Database) │
                    └─────────────────┘
```

### 核心组件

#### 1. Web界面层
- **技术栈**: Streamlit
- **职责**: 用户交互、数据展示、配置管理
- **组件**: 页面组件、工具函数、状态管理

#### 2. 代理系统层
- **技术栈**: Python + LLM APIs
- **职责**: 专业分析、决策制定、报告生成
- **代理**: 技术分析师、链上分析师、情绪分析师等

#### 3. 数据源层
- **技术栈**: CCXT + REST APIs
- **职责**: 数据获取、数据清洗、数据缓存
- **数据源**: 交易所、链上数据、情绪数据等

#### 4. 核心引擎层
- **技术栈**: Python + 异步处理
- **职责**: 任务调度、结果聚合、错误处理
- **功能**: 分析协调、进度跟踪、结果管理

#### 5. 数据存储层
- **技术栈**: JSON文件系统
- **职责**: 数据持久化、缓存管理、配置存储
- **数据**: 分析结果、用户配置、会话状态

## 🛠️ 开发环境设置

### 前置要求
```bash
# Python 3.8+
python --version

# Git
git --version

# 代码编辑器 (推荐)
# VS Code, PyCharm, 或其他支持Python的编辑器
```

### 开发环境安装
```bash
# 克隆项目
git clone <repository-url>
cd crypto_trading_agents

# 创建虚拟环境
python -m venv dev_env
source dev_env/bin/activate  # Windows: dev_env\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements_web.txt
pip install pytest pytest-cov black flake8 mypy

# 安装预提交钩子
pip install pre-commit
pre-commit install
```

### VS Code配置
```json
{
    "python.defaultInterpreterPath": "./dev_env/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## 📁 代码结构详解

### 目录结构
```
crypto_trading_agents/
├── crypto_trading_agents/          # 主要代码
│   ├── agents/                     # 代理实现
│   │   ├── analysts/              # 分析师代理
│   │   │   ├── technical_analyst.py
│   │   │   ├── onchain_analyst.py
│   │   │   ├── sentiment_analyst.py
│   │   │   ├── defi_analyst.py
│   │   │   └── market_maker_analyst.py
│   │   ├── managers/              # 管理器代理
│   │   ├── researchers/           # 研究员代理
│   │   └── utils/                 # 代理工具
│   ├── config/                    # 配置管理
│   ├── src/
│   │   ├── data_sources/          # 数据源实现
│   │   ├── crypto_data_sources.py
│   │   ├── exchange_data_sources.py
│   │   └── __init__.py
│   │   └── database/              # 数据库模型
│   │   ├── models.py
│   │   ├── utils.py
│   │   └── __init__.py
│   ├── llm/                       # LLM适配器
│   ├── tools/                     # 工具函数
│   ├── web/                       # Web界面
│   │   ├── app.py                 # 主应用
│   │   ├── components/            # 组件
│   │   └── utils/                 # 工具函数
│   └── utils/                     # 通用工具
├── tests/                         # 测试文件
├── docs/                          # 文档
├── examples/                      # 示例代码
└── scripts/                       # 脚本文件
```

### 核心类说明

#### 代理基类
```python
class BaseAgent:
    """代理基类"""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
    
    async def analyze(self, data: dict) -> dict:
        """分析方法 - 子类必须实现"""
        raise NotImplementedError
```

#### 数据源基类
```python
class BaseDataSource:
    """数据源基类"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
    
    def get_data(self, **kwargs) -> dict:
        """获取数据 - 子类必须实现"""
        raise NotImplementedError
```

#### 数据库模型
```python
class AnalysisResult:
    """分析结果模型"""
    
    def __init__(self, analysis_id: str, symbol: str, agents: list):
        self.analysis_id = analysis_id
        self.symbol = symbol
        self.agents = agents
        self.results = {}
        self.status = "pending"
```

## 🔧 开发指南

### 添加新的分析代理

#### 1. 创建代理文件
```python
# crypto_trading_agents/agents/analysts/new_analyst.py
from ..base_agent import BaseAgent
from typing import Dict, Any

class NewAnalyst(BaseAgent):
    """新分析师代理"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("new_analyst", config)
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """实现分析方法"""
        # 分析逻辑
        return {
            "analysis_type": "new_analysis",
            "result": "analysis_result",
            "confidence": 0.85
        }
```

#### 2. 注册代理
```python
# crypto_trading_agents/agents/__init__.py
from .analysts.new_analyst import NewAnalyst

# 添加到代理注册表
AGENT_REGISTRY = {
    "new_analyst": NewAnalyst,
    # ... 其他代理
}
```

#### 3. 更新Web界面
```python
# web/components/analysis_form.py
def get_available_agents():
    """获取可用代理列表"""
    return [
        "technical_analyst",
        "onchain_analyst",
        "sentiment_analyst",
        "defi_analyst",
        "market_maker_analyst",
        "new_analyst"  # 添加新代理
    ]
```

### 添加新的数据源

#### 1. 创建数据源文件
```python
# src/data_sources/new_data_source.py
from .crypto_data_sources import BaseDataSource
import requests

class NewDataSource(BaseDataSource):
    """新数据源"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key, "https://api.newsource.com/v1")
    
    def get_price_data(self, symbol: str) -> dict:
        """获取价格数据"""
        url = f"{self.base_url}/price"
        params = {"symbol": symbol}
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        return self.make_request(url, params)
```

#### 2. 注册数据源
```python
# src/data_sources/__init__.py
from .new_data_source import NewDataSource

# 添加到数据源管理器
data_source_manager.register_data_source("new_source", NewDataSource())
```

### 添加新的Web组件

#### 1. 创建组件文件
```python
# web/components/new_component.py
import streamlit as st

def render_new_component():
    """渲染新组件"""
    st.subheader("新组件")
    
    # 组件逻辑
    user_input = st.text_input("输入内容")
    if user_input:
        st.write(f"您输入了: {user_input}")
```

#### 2. 集成到主应用
```python
# web/app.py
from components.new_component import render_new_component

def main():
    # ... 其他代码
    
    # 添加新组件
    render_new_component()
```

## 🧪 测试指南

### 单元测试

#### 创建测试文件
```python
# tests/test_new_analyst.py
import pytest
from src.crypto_trading_agents.agents.analysts.new_analyst import NewAnalyst

@pytest.fixture
def analyst():
    """创建测试用的分析师实例"""
    config = {"param1": "value1"}
    return NewAnalyst(config)

@pytest.mark.asyncio
async def test_analyze(analyst):
    """测试分析方法"""
    test_data = {"symbol": "BTC/USDT"}
    result = await analyst.analyze(test_data)
    
    assert "analysis_type" in result
    assert "result" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
```

#### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_new_analyst.py

# 生成覆盖率报告
pytest --cov=crypto_trading_agents --cov-report=html
```

### 集成测试

#### 测试数据源
```python
# tests/test_data_sources.py
import pytest
from src.data_sources import data_source_manager

def test_price_data():
    """测试价格数据获取"""
    result = data_source_manager.get_price_data("BTC/USDT")
    assert result is not None
    assert "price" in result
```

#### 测试Web界面
```python
# tests/test_web_app.py
from src.crypto_trading_agents.web.app import main

def test_web_app():
    """测试Web应用"""
    # 这里可以使用Streamlit的测试工具
    pass
```

## 🚀 部署指南

### Docker部署

#### 创建Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
COPY requirements_web.txt .

# 安装依赖
RUN pip install -r requirements.txt
RUN pip install -r requirements_web.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/analysis data/sessions data/config

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["python", "start_web.py"]
```

#### 构建和运行
```bash
# 构建镜像
docker build -t crypto-trading-agents .

# 运行容器
docker run -p 8501:8501 -v $(pwd)/data:/app/data crypto-trading-agents
```

### 云服务部署

#### AWS部署
```bash
# 使用ECS
aws ecs create-cluster --cluster-name crypto-trading-agents

# 使用EKS
eksctl create cluster --name crypto-trading-agents

# 使用Lambda (Serverless)
aws lambda create-function --function-name crypto-agents
```

#### GCP部署
```bash
# 使用Cloud Run
gcloud run deploy crypto-trading-agents --image gcr.io/PROJECT-ID/crypto-agents

# 使用GKE
gcloud container clusters create crypto-agents-cluster
```

## 🔍 调试指南

### 日志配置
```python
# config/logging_config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_agents.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 调试技巧

#### 1. 使用调试器
```python
import pdb

def debug_function():
    pdb.set_trace()  # 断点
    # 调试代码
```

#### 2. 性能分析
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 要分析的代码
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

#### 3. 内存分析
```python
import tracemalloc

def memory_profile():
    tracemalloc.start()
    
    # 要分析的代码
    
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    for stat in top_stats[:10]:
        print(stat)
```

## 📚 最佳实践

### 代码质量

#### 1. 代码风格
```bash
# 使用black格式化代码
black crypto_trading_agents/

# 使用flake8检查代码
flake8 crypto_trading_agents/

# 使用mypy进行类型检查
mypy crypto_trading_agents/
```

#### 2. 文档规范
```python
def analyze_data(data: dict) -> dict:
    """
    分析数据
    
    Args:
        data: 要分析的数据字典
        
    Returns:
        分析结果字典
        
    Raises:
        ValueError: 当数据格式不正确时
    """
    if not isinstance(data, dict):
        raise ValueError("数据必须是字典类型")
    
    # 实现逻辑
    return {"result": "success"}
```

#### 3. 错误处理
```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def safe_api_call(url: str) -> Optional[dict]:
    """
    安全的API调用
    
    Args:
        url: API URL
        
    Returns:
        API响应数据或None
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API调用失败: {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON解析失败: {e}")
        return None
```

### 性能优化

#### 1. 缓存策略
```python
from functools import lru_cache
import time

@lru_cache(maxsize=1000)
def expensive_computation(param: str) -> dict:
    """昂贵的计算函数"""
    # 缓存结果
    return {"result": param.upper(), "timestamp": time.time()}
```

#### 2. 异步处理
```python
import asyncio
import aiohttp

async def fetch_multiple(urls: list) -> list:
    """异步获取多个URL"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_url(session, url: str) -> dict:
    """获取单个URL"""
    async with session.get(url) as response:
        return await response.json()
```

#### 3. 数据库优化
```python
# 使用索引提高查询性能
# 批量操作减少数据库访问
# 使用连接池管理数据库连接
```

### 安全考虑

#### 1. API密钥安全
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY环境变量未设置")
```

#### 2. 输入验证
```python
import re

def validate_symbol(symbol: str) -> bool:
    """验证交易对符号"""
    pattern = r'^[A-Z]{2,10}/[A-Z]{3,10}$'
    return re.match(pattern, symbol) is not None
```

#### 3. 异常处理
```python
import sys
import traceback

def handle_exception(func):
    """异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"错误发生: {e}")
            print(traceback.format_exc())
            sys.exit(1)
    return wrapper
```

## 🤝 贡献指南

### 提交规范

#### 1. 分支命名
```
feature/添加新功能
bugfix/修复问题
docs/文档更新
test/测试相关
```

#### 2. 提交信息
```
类型(范围): 简短描述

详细描述（可选）

Closes #123
```

类型说明：
- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建或工具变动

#### 3. Pull Request模板
```markdown
## 变更描述
简要描述这个PR的目的和变更内容

## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 测试更新

## 测试清单
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过

## 相关Issue
Closes #123

## 截图（如适用）
<!-- 添加截图展示变更效果 -->
```

### 代码审查清单

#### 代码质量
- [ ] 代码符合PEP 8规范
- [ ] 函数和类有适当的文档字符串
- [ ] 变量和函数命名清晰
- [ ] 代码逻辑清晰易懂

#### 功能正确性
- [ ] 功能实现符合需求
- [ ] 边界情况处理正确
- [ ] 错误处理完善
- [ ] 性能影响可接受

#### 测试覆盖
- [ ] 有相应的单元测试
- [ ] 测试覆盖率达标
- [ ] 集成测试通过
- [ ] 手动测试通过

---

## 🎉 开发完成！

恭喜您完成了开发者指南的学习。现在您可以：

1. **开始开发**: 创建新功能和修复问题
2. **运行测试**: 确保代码质量
3. **提交代码**: 贡献到项目
4. **参与讨论**: 与其他开发者交流

如果您有任何问题，请参考相关文档或联系开发团队。祝您开发愉快！
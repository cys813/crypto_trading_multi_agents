# 加密货币交易系统代码规范和约定

## 编程语言和版本
- **主语言**: Python 3.8+
- **编码格式**: UTF-8
- **行结束符**: LF (Unix风格)

## 命名约定

### 文件命名
- **Python文件**: 使用snake_case，例如：`market_analysis_agent.py`, `strategy_executor.py`
- **配置文件**: 使用snake_case或kebab-case，例如：`config.json`, `trading-config.yml`
- **测试文件**: 以`test_`开头，例如：`test_market_analysis.py`, `test_strategy_execution.py`

### 变量和函数命名
- **变量**: 使用snake_case，例如：`market_data`, `trading_signal`, `risk_level`
- **函数**: 使用snake_case，动词开头，例如：`calculate_indicators()`, `execute_order()`, `assess_risk()`
- **私有变量/函数**: 以下划线开头，例如：`_internal_data`, `_calculate_private_metric()`

### 类命名
- **类名**: 使用PascalCase，例如：`MarketAnalysisAgent`, `StrategyExecutionAgent`, `RiskController`
- **异常类**: 使用PascalCase，以Error结尾，例如：`TradingError`, `DataValidationError`

### 常量命名
- **常量**: 使用大写SNAKE_CASE，例如：`MAX_POSITION_SIZE`, `DEFAULT_RISK_LEVEL`, `API_TIMEOUT`

## 代码格式化

### 行长度
- **最大行长度**: 88字符 (Black默认)
- **例外情况**: 导入语句、长字符串、注释可适当放宽

### 缩进
- **缩进**: 4个空格
- **连续行**: 8个空格或与括号对齐

### 空行
- **函数间**: 2个空行
- **类间**: 2个空行
- **方法间**: 1个空行
- **逻辑块间**: 1个空行

### 空格使用
- **操作符两侧**: 添加空格，例如：`a + b`, `x * y`
- **逗号后**: 添加空格，例如：`func(a, b, c)`
- **函数参数**: 逗号后添加空格，例如：`def func(param1, param2):`
- **括号内**: 不添加空格，例如：`if (condition):`, `for item in items:`

## 类型提示

### 基本规则
- **所有函数**: 都应该有类型提示
- **复杂类型**: 使用`typing`模块，例如：`List[str]`, `Dict[str, float]`, `Optional[int]`
- **返回类型**: 始终明确指定，例如：`-> bool`, `-> List[Dict]`

### 类型提示示例
```python
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd
import numpy as np

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """计算相对强弱指数 (RSI)"""
    pass

def analyze_market_data(data: Dict[str, Union[float, int]]) -> Dict[str, float]:
    """分析市场数据"""
    pass

def execute_trade(symbol: str, quantity: float, order_type: str) -> Optional[Dict]:
    """执行交易"""
    pass
```

## 文档字符串规范

### Google风格文档字符串
```python
def calculate_moving_average(data: pd.Series, window: int = 20) -> pd.Series:
    """计算简单移动平均线。
    
    Args:
        data: 价格数据的时间序列
        window: 移动平均的窗口大小，默认为20
        
    Returns:
        pd.Series: 计算后的移动平均线序列
        
    Raises:
        ValueError: 当窗口大小超过数据长度时抛出
        
    Examples:
        >>> prices = pd.Series([1, 2, 3, 4, 5])
        >>> ma = calculate_moving_average(prices, window=3)
        >>> print(ma.iloc[2])
        2.0
    """
    pass
```

### 类文档字符串
```python
class MarketAnalysisAgent:
    """市场分析Agent类。
    
    这个Agent负责实时监控加密货币市场数据，计算技术指标，
    识别市场趋势并生成交易信号。
    
    Attributes:
        api_client: API客户端对象
        config: 配置字典
        is_running: 运行状态标志
        
    Examples:
        >>> agent = MarketAnalysisAgent(config)
        >>> agent.start()
        >>> signal = agent.get_trading_signal()
    """
    pass
```

## 导入规范

### 导入顺序
1. **标准库导入**: 如`import os`, `import sys`
2. **第三方库导入**: 如`import pandas as pd`, `import numpy as np`
3. **本地模块导入**: 如`from src.agents.market_analysis import MarketAnalysisAgent`

### 导入示例
```python
# 标准库
import os
import sys
import logging
from typing import List, Dict, Optional

# 第三方库
import pandas as pd
import numpy as np
import aiohttp
import async_timeout

# 本地模块
from src.agents.market_analysis import MarketAnalysisAgent
from src.utils.data_processing import clean_market_data
from src.config.settings import TRADING_CONFIG
```

### 禁止的导入方式
- **避免使用通配符导入**: `from module import *`
- **避免使用相对导入**: `from ..module import something`
- **避免使用过长导入行**: 保持导入语句简洁

## 错误处理

### 异常处理原则
```python
try:
    result = risky_operation()
except ValueError as e:
    logging.error(f"数值错误: {e}")
    raise TradingError(f"交易失败: {e}") from e
except Exception as e:
    logging.error(f"未知错误: {e}")
    raise
```

### 自定义异常
```python
class TradingError(Exception):
    """交易相关错误的基础类"""
    pass

class DataValidationError(TradingError):
    """数据验证错误"""
    pass

class RiskLimitExceeded(TradingError):
    """风险限制超出错误"""
    pass
```

## 日志记录

### 日志级别使用
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息，如系统启动、操作完成
- **WARNING**: 警告信息，如配置问题、潜在风险
- **ERROR**: 错误信息，如操作失败、数据错误
- **CRITICAL**: 严重错误，如系统崩溃、数据丢失

### 日志格式
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用日志
logger.info("系统启动成功")
logger.warning("检测到异常市场波动")
logger.error("交易执行失败: %s", error_message)
```

## 异步编程规范

### 异步函数命名
- **异步函数**: 在函数名前添加`async_`前缀或使用`_async`后缀
- **协程**: 使用`async def`定义
- **异步上下文管理器**: 使用`async with`

### 异步编程示例
```python
import asyncio
import aiohttp

async def async_fetch_market_data(symbol: str) -> Dict[str, float]:
    """异步获取市场数据"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/{symbol}") as response:
            return await response.json()

async def process_multiple_symbols(symbols: List[str]) -> List[Dict]:
    """并行处理多个交易对"""
    tasks = [async_fetch_market_data(symbol) for symbol in symbols]
    return await asyncio.gather(*tasks)
```

## 测试规范

### 测试文件命名
- **单元测试**: `test_<module_name>.py`
- **集成测试**: `test_integration_<feature>.py`
- **性能测试**: `test_performance_<component>.py`

### 测试函数命名
- **测试函数**: `test_<function_name>_<scenario>`
- **测试类**: `Test<ClassName>`

### 测试示例
```python
import pytest
import pandas as pd
from src.agents.market_analysis import MarketAnalysisAgent

class TestMarketAnalysisAgent:
    """市场分析Agent测试类"""
    
    @pytest.fixture
    def agent(self):
        """创建测试Agent实例"""
        config = {"risk_level": "low"}
        return MarketAnalysisAgent(config)
    
    def test_calculate_rsi(self, agent):
        """测试RSI计算功能"""
        prices = pd.Series([1, 2, 3, 4, 5])
        rsi = agent.calculate_rsi(prices)
        assert isinstance(rsi, pd.Series)
        assert not rsi.isna().all()
    
    @pytest.mark.asyncio
    async def test_async_data_fetch(self, agent):
        """测试异步数据获取功能"""
        data = await agent.async_fetch_data("BTCUSDT")
        assert isinstance(data, dict)
        assert "price" in data
```

## 配置管理

### 配置文件规范
- **主配置**: `config.json` 或 `config.yml`
- **环境配置**: `config.<env>.json` (如 `config.dev.json`)
- **敏感配置**: 使用环境变量或加密存储

### 配置示例
```python
import json
from pathlib import Path

def load_config(config_path: str = "config.json") -> Dict:
    """加载配置文件"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# 使用配置
config = load_config()
risk_level = config.get("risk_level", "medium")
api_timeout = config.get("api_timeout", 30)
```

## 代码审查清单

### 功能审查
- [ ] 代码功能是否符合需求
- [ ] 是否处理了边界情况
- [ ] 是否有适当的错误处理
- [ ] 是否遵循了DRY原则

### 质量审查
- [ ] 代码是否清晰易懂
- [ ] 变量和函数命名是否合理
- [ ] 是否有适当的注释和文档
- [ ] 是否遵循了代码风格规范

### 性能审查
- [ ] 是否考虑了性能问题
- [ ] 是否有不必要的计算
- [ ] 是否使用了合适的数据结构
- [ ] 异步操作是否正确使用

### 安全审查
- [ ] 是否有安全漏洞
- [ ] 敏感信息是否正确处理
- [ ] 输入验证是否充分
- [ ] 权限控制是否适当

## 持续集成检查

### 提交前检查
- [ ] 运行 `black` 格式化代码
- [ ] 运行 `isort` 排序导入
- [ ] 运行 `flake8` 检查代码质量
- [ ] 运行 `mypy` 检查类型
- [ ] 运行 `pytest` 运行测试

### 提交消息规范
```
类型(范围): 简短描述

详细描述（可选）

相关工单: #123
```

类型包括：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具
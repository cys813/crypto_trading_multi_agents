"""
默认配置文件 - 统一配置系统入口

此文件保持向后兼容性，所有配置已迁移至unified_config.py
"""

from typing import Dict, Any
from .unified_config import get_unified_config

# 默认配置 - 使用统一配置
DEFAULT_CONFIG: Dict[str, Any] = get_unified_config()

def get_config(market_condition: str = "normal", llm_provider: str = None) -> Dict[str, Any]:
    """
    获取配置，可以根据市场条件和LLM提供商调整
    
    Args:
        market_condition: 市场条件 ('bull_market', 'bear_market', 'sideways_market', 'high_volatility')
        llm_provider: LLM提供商 ('zhipuai', 'dashscope', 'deepseek', 'traditional')
    
    Returns:
        配置字典
    """
    return get_unified_config(market_condition=market_condition, llm_provider=llm_provider)

def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置的有效性，委托给unified_config.py
    
    Args:
        config: 配置字典
    
    Returns:
        是否有效
    """
    from unified_config import validate_config as _validate_config
    return _validate_config(config)
"""
统一配置文件 - 直接使用config.json

所有配置已集中到项目根目录的config.json文件中。
此模块提供便捷的配置访问接口，保持向后兼容性。
"""

from typing import Dict, Any, Optional, List
from .json_config import JSONConfigLoader

# 全局配置加载器实例
_config_loader = JSONConfigLoader()

def get_unified_config(market_condition: str = "normal", llm_provider: str = None) -> Dict[str, Any]:
    """
    获取统一配置，可以根据市场条件和LLM提供商调整
    
    Args:
        market_condition: 市场条件 ('bull_market', 'bear_market', 'sideways_market', 'high_volatility')
        llm_provider: LLM提供商 ('zhipuai', 'dashscope', 'deepseek', 'traditional')
    
    Returns:
        配置字典
    """
    return _config_loader.get_config(market_condition=market_condition, llm_provider=llm_provider)

def get_config_template(template_name: str = "default") -> Dict[str, Any]:
    """
    获取配置模板
    
    Args:
        template_name: 模板名称
            - 'zhipuai': 使用智谱AI
            - 'dashscope': 使用通义千问
            - 'deepseek': 使用DeepSeek
            - 'traditional': 仅传统分析，不使用AI
            - 'default': 默认配置
    
    Returns:
        配置字典
    """
    return _config_loader.get_config_template(template_name)

def get_llm_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """
    获取指定LLM提供商的配置
    
    Args:
        provider: LLM提供商名称，为None时使用默认提供商
    
    Returns:
        LLM配置字典
    """
    return _config_loader.get_llm_config(provider)

def get_available_llm_providers() -> List[str]:
    """
    获取所有可用的LLM提供商列表
    
    Returns:
        LLM提供商名称列表
    """
    return _config_loader.get_available_llm_providers()

def validate_config(config: Dict[str, Any] = None) -> bool:
    """
    验证配置的有效性
    
    Args:
        config: 配置字典，为None时使用当前配置
        
    Returns:
        是否有效
    """
    return _config_loader.validate_config(config)

def print_config_info():
    """打印配置信息，用于调试"""
    _config_loader.print_config_info()

def get_config_with_llm(llm_provider: str) -> Dict[str, Any]:
    """
    获取指定LLM提供商的完整配置
    
    Args:
        llm_provider: LLM提供商 ('zhipuai', 'dashscope', 'deepseek', 'traditional')
    
    Returns:
        完整配置字典
    """
    return get_unified_config(llm_provider=llm_provider)

def reload_config():
    """重新加载配置文件"""
    global _config_loader
    _config_loader = JSONConfigLoader()
    return _config_loader.get_config(reload=True)

# 向后兼容性函数
def set_default_llm_provider(provider: str) -> Dict[str, Any]:
    """
    设置默认LLM提供商
    注意: 需要手动修改config.json文件中的 llm.default_provider
    
    Args:
        provider: LLM提供商名称
    
    Returns:
        当前配置
    """
    print(f"提示: 请手动修改config.json中的 'llm.default_provider' 为 '{provider}'")
    return get_unified_config()

def deep_merge(base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
    """
    深度合并字典 (已废弃，建议使用JSON预设配置)
    
    Args:
        base_dict: 基础字典
        update_dict: 更新字典
    """
    print("警告: deep_merge函数已废弃，建议在config.json中使用预设配置")
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            deep_merge(base_dict[key], value)
        else:
            base_dict[key] = value

# 兼容性属性 - 动态获取配置
@property
def UNIFIED_CONFIG() -> Dict[str, Any]:
    """获取统一配置 (兼容性属性)"""
    return get_unified_config()

@property  
def LLM_PRESETS() -> Dict[str, Any]:
    """获取LLM预设配置 (兼容性属性)"""
    config = get_unified_config()
    return config.get("presets", {}).get("llm", {})

@property
def MARKET_PRESETS() -> Dict[str, Any]:
    """获取市场条件预设配置 (兼容性属性)"""
    config = get_unified_config()
    return config.get("presets", {}).get("market_conditions", {})

# 设置模块级别的属性（不推荐使用，建议直接调用函数）
import sys
module = sys.modules[__name__]
module.UNIFIED_CONFIG = UNIFIED_CONFIG
module.LLM_PRESETS = LLM_PRESETS
module.MARKET_PRESETS = MARKET_PRESETS
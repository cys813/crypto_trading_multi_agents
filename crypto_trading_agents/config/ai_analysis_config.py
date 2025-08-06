"""
统一LLM服务和AI分析配置
"""

import os
from typing import Dict, Any

def get_unified_llm_service_config() -> Dict[str, Any]:
    """
    获取统一LLM服务配置
    
    Returns:
        统一LLM服务配置字典
    """
    return {
        # 统一LLM服务配置
        "llm_service_config": {
            "default_provider": "dashscope",  # 默认LLM提供商
            "providers": {
                "dashscope": {
                    "api_key": os.getenv("DASHSCOPE_API_KEY"),
                    "model": "qwen-plus",
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                "deepseek": {
                    "api_key": os.getenv("DEEPSEEK_API_KEY"), 
                    "model": "deepseek-chat",
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            }
        },
        
        # AI分析总开关和通用配置
        "ai_analysis_config": {
            "enabled": True,  # 是否启用AI增强分析
            "temperature": 0.3,  # 默认AI模型温度参数
            "max_tokens": 2000,  # 默认最大生成token数
            "retry_attempts": 2,  # 失败重试次数
            "fallback_to_traditional": True,  # AI失败时是否回退到传统分析
        },
        
        # 分析配置
        "analysis_config": {
            "technical_indicators": [
                "rsi", "macd", "bollinger_bands", 
                "stochastic", "williams_r"
            ],
            "sentiment_sources": [
                "twitter", "reddit", "telegram", "discord", "news"
            ],
            "bull_indicators": [
                "price_momentum", "volume_breakout", "market_structure",
                "institutional_inflows", "regulatory_catalysts", "technical_breakouts", "sentiment_shift"
            ],
            "bear_indicators": [
                "price_decline", "volume_distribution", "market_breakdown",
                "institutional_outflows", "regulatory_crackdown", "technical_breakdown", "panic_sentiment"
            ],
            "confidence_weights": {
                "signal_strength": 0.4,
                "data_quality": 0.4,
                "model_accuracy": 0.2
            },
            "data_quality_weights": {
                "completeness": 0.3,
                "freshness": 0.4,
                "accuracy": 0.3
            }
        },
        
        # 分层数据配置
        "layered_data_config": {
            "enabled": True,  # 是否启用分层数据
            "cache_duration": 3600,  # 缓存时长（秒）
        }
    }

def get_ai_analysis_config() -> Dict[str, Any]:
    """
    获取AI分析配置（向后兼容）
    
    Returns:
        AI分析配置字典
    """
    return get_unified_llm_service_config()

def get_dashscope_config() -> Dict[str, Any]:
    """
    获取阿里百炼专用配置
    
    Returns:
        DashScope配置字典
    """
    base_config = get_unified_llm_service_config()
    base_config["llm_service_config"]["default_provider"] = "dashscope"
    return base_config

def get_deepseek_config() -> Dict[str, Any]:
    """
    获取DeepSeek专用配置
    
    Returns:
        DeepSeek配置字典
    """
    base_config = get_unified_llm_service_config()
    base_config["llm_service_config"]["default_provider"] = "deepseek"
    return base_config

def get_traditional_only_config() -> Dict[str, Any]:
    """
    获取纯传统技术分析配置（不使用AI）
    
    Returns:
        传统分析配置字典
    """
    base_config = get_unified_llm_service_config()
    base_config["ai_analysis_config"]["enabled"] = False
    return base_config

# 配置模板
CONFIG_TEMPLATES = {
    "unified": get_unified_llm_service_config(),
    "ai_enhanced": get_ai_analysis_config(),
    "dashscope": get_dashscope_config(),
    "deepseek": get_deepseek_config(),
    "traditional": get_traditional_only_config()
}

def get_config_template(template_name: str = "unified") -> Dict[str, Any]:
    """
    获取配置模板
    
    Args:
        template_name: 模板名称 (unified, ai_enhanced, dashscope, deepseek, traditional)
        
    Returns:
        配置字典
    """
    return CONFIG_TEMPLATES.get(template_name, get_unified_llm_service_config())
"""
API密钥检查工具
"""

import os
from typing import Dict, Any, List

def check_api_keys() -> Dict[str, Any]:
    """检查API密钥配置状态"""
    
    # 必需的API密钥
    required_keys = {
        'AI模型密钥': ['OPENAI_API_KEY', 'DASHSCOPE_API_KEY', 'DEEPSEEK_API_KEY'],
        '加密货币数据': ['COINGECKO_API_KEY', 'BINANCE_API_KEY', 'COINMARKETCAP_API_KEY'],
        '链上数据': ['GLASSNODE_API_KEY', 'INTOTHEBLOCK_API_KEY'],
        '情绪数据': ['LUNARCRUSH_API_KEY', 'SANTIMENT_API_KEY']
    }
    
    # 检查每个类别的API密钥
    status = {
        'all_configured': True,
        'details': {}
    }
    
    for category, keys in required_keys.items():
        category_configured = False
        configured_key = None
        
        for key in keys:
            if os.getenv(key):
                category_configured = True
                configured_key = key
                break
        
        if not category_configured:
            status['all_configured'] = False
            status['details'][category] = {
                'configured': False,
                'display': '未配置',
                'keys': keys
            }
        else:
            status['details'][category] = {
                'configured': True,
                'display': f'✅ {configured_key}',
                'keys': keys
            }
    
    # 检查可选API密钥
    optional_keys = [
        'NEWS_API_KEY',
        'TWITTER_API_KEY',
        'REDDIT_API_KEY',
        'TELEGRAM_API_KEY'
    ]
    
    status['optional'] = {}
    for key in optional_keys:
        configured = bool(os.getenv(key))
        status['optional'][key] = {
            'configured': configured,
            'display': '✅ 已配置' if configured else '❌ 未配置'
        }
    
    return status

def get_api_key_status() -> Dict[str, Any]:
    """获取详细的API密钥状态"""
    
    all_keys = [
        'OPENAI_API_KEY',
        'DASHSCOPE_API_KEY', 
        'DEEPSEEK_API_KEY',
        'COINGECKO_API_KEY',
        'BINANCE_API_KEY',
        'COINMARKETCAP_API_KEY',
        'GLASSNODE_API_KEY',
        'INTOTHEBLOCK_API_KEY',
        'LUNARCRUSH_API_KEY',
        'SANTIMENT_API_KEY',
        'NEWS_API_KEY',
        'TWITTER_API_KEY',
        'REDDIT_API_KEY',
        'TELEGRAM_API_KEY'
    ]
    
    key_status = {}
    for key in all_keys:
        value = os.getenv(key)
        if value:
            # 隐藏API密钥的具体值，只显示前几位
            masked_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
            key_status[key] = {
                'configured': True,
                'value': masked_value,
                'length': len(value)
            }
        else:
            key_status[key] = {
                'configured': False,
                'value': None,
                'length': 0
            }
    
    return key_status

def validate_api_configuration() -> List[str]:
    """验证API配置，返回错误列表"""
    
    errors = []
    
    # 检查是否至少有一个AI模型API密钥
    ai_keys = ['OPENAI_API_KEY', 'DASHSCOPE_API_KEY', 'DEEPSEEK_API_KEY']
    if not any(os.getenv(key) for key in ai_keys):
        errors.append("至少需要配置一个AI模型API密钥（OPENAI_API_KEY、DASHSCOPE_API_KEY或DEEPSEEK_API_KEY）")
    
    # 检查是否至少有一个加密货币数据API密钥
    crypto_keys = ['COINGECKO_API_KEY', 'BINANCE_API_KEY', 'COINMARKETCAP_API_KEY']
    if not any(os.getenv(key) for key in crypto_keys):
        errors.append("至少需要配置一个加密货币数据API密钥（COINGECKO_API_KEY、BINANCE_API_KEY或COINMARKETCAP_API_KEY）")
    
    # 检查API密钥格式
    for key in ai_keys + crypto_keys:
        value = os.getenv(key)
        if value and len(value) < 10:
            errors.append(f"{key} 格式可能不正确（长度过短）")
    
    return errors
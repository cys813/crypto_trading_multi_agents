#!/usr/bin/env python3
"""
诊断AI分析功能为什么没有工作
"""
import sys
import os
sys.path.insert(0, './src')

from crypto_trading_agents.default_config import DEFAULT_CONFIG
from crypto_trading_agents.unified_config import get_unified_config
from crypto_trading_agents.services.llm_service import llm_service, is_llm_service_available
import os

def diagnose_ai_setup():
    """诊断AI设置"""
    print('🔍 诊断AI分析功能设置...')
    print('=' * 60)

    # 1. 检查环境变量
    print('1. 环境变量检查:')
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    print(f'   DASHSCOPE_API_KEY: {"✅ 已设置" if dashscope_key else "❌ 未设置"}')
    print(f'   DEEPSEEK_API_KEY: {"✅ 已设置" if deepseek_key else "❌ 未设置"}')
    print(f'   OPENAI_API_KEY: {"✅ 已设置" if openai_key else "❌ 未设置"}')

    # 2. 检查LLM服务状态
    print('\n2. LLM服务状态:')
    print(f'   LLM服务可用性: {"✅ 可用" if is_llm_service_available() else "❌ 不可用"}')
    print(f'   已初始化适配器数: {len(llm_service.llm_adapters)}')
    if llm_service.llm_adapters:
        print(f'   可用适配器: {list(llm_service.llm_adapters.keys())}')
        print(f'   默认提供者: {llm_service.default_provider}')
    else:
        print('   没有可用的LLM适配器')

    # 3. 检查配置
    print('\n3. 配置检查:')
    # 获取统一配置
    unified_config = get_unified_config()
    print(f'   统一配置AI启用: {unified_config.get("ai_analysis_config", {}).get("enabled", False)}')

    # 检查默认配置中的LLM相关设置
    llm_provider = DEFAULT_CONFIG.get('llm_provider', '未设置')
    deep_think_llm = DEFAULT_CONFIG.get('deep_think_llm', '未设置')
    quick_think_llm = DEFAULT_CONFIG.get('quick_think_llm', '未设置')
    print(f'   LLM提供者: {llm_provider}')
    print(f'   深度思考模型: {deep_think_llm}')
    print(f'   快速思考模型: {quick_think_llm}')

    # 4. 检查LLM服务配置
    llm_service_config = unified_config.get('llm_service_config')
    if llm_service_config:
        print('\n4. LLM服务配置详情:')
        print(f'   默认提供者: {llm_service_config.get("default_provider", "未设置")}')
        providers = llm_service_config.get('providers', {})
        print(f'   配置的提供者: {list(providers.keys())}')
        for provider, config in providers.items():
            api_key = config.get('api_key')
            model = config.get('model', '未设置')
            has_key = api_key and api_key.strip() != ''
            print(f'   - {provider}: API密钥{"✅" if has_key else "❌"}, 模型: {model}')
    else:
        print('\n4. 未找到LLM服务配置')

    print('\n' + '=' * 60)
    print('诊断完成')

if __name__ == "__main__":
    diagnose_ai_setup()
#!/usr/bin/env python3
"""
智谱AI集成测试脚本
"""
import sys
import os
sys.path.insert(0, './src')

from crypto_trading_agents.config.ai_analysis_config import get_config_template, get_zhipuai_config
from crypto_trading_agents.services.llm_service import llm_service, initialize_llm_service, is_llm_service_available
import os

def test_zhipuai_setup():
    """测试智谱AI设置"""
    print('🔍 测试智谱AI集成...')
    print('=' * 60)

    # 1. 检查环境变量
    print('1. 环境变量检查:')
    zhipuai_key = os.getenv('ZHIPUAI_API_KEY')
    print(f'   ZHIPUAI_API_KEY: {"✅ 已设置" if zhipuai_key else "❌ 未设置"}')
    
    if not zhipuai_key:
        print('   ⚠️  请设置ZHIPUAI_API_KEY环境变量:')
        print('   export ZHIPUAI_API_KEY="your_zhipuai_api_key"')
        return False

    # 2. 获取智谱AI配置
    print('\n2. 获取智谱AI配置:')
    config = get_zhipuai_config()
    llm_config = config.get('llm_service_config', {})
    providers = llm_config.get('providers', {})
    zhipuai_config = providers.get('zhipuai', {})
    
    print(f'   默认提供商: {llm_config.get("default_provider", "未设置")}')
    print(f'   模型: {zhipuai_config.get("model", "未设置")}')
    print(f'   API密钥: {"✅ 已配置" if zhipuai_config.get("api_key") else "❌ 未配置"}')

    # 3. 初始化LLM服务
    print('\n3. 初始化LLM服务:')
    success = initialize_llm_service(llm_config)
    print(f'   初始化结果: {"✅ 成功" if success else "❌ 失败"}')
    
    if not success:
        print('   ❌ LLM服务初始化失败')
        return False

    # 4. 检查服务状态
    print('\n4. LLM服务状态:')
    available = is_llm_service_available()
    print(f'   服务可用性: {"✅ 可用" if available else "❌ 不可用"}')
    print(f'   可用适配器数: {len(llm_service.llm_adapters)}')
    
    if llm_service.llm_adapters:
        print(f'   可用适配器: {list(llm_service.llm_adapters.keys())}')
        print(f'   默认提供商: {llm_service.default_provider}')
    else:
        print('   ❌ 没有可用的LLM适配器')
        return False

    # 5. 测试简单的LLM调用
    print('\n5. LLM调用测试:')
    try:
        print('   发送简单测试请求...')
        response = llm_service.call_llm(
            "请用一个词回答：比特币的前景如何？", 
            provider="zhipuai",
            temperature=0.1, 
            max_tokens=50
        )
        print(f'   ✅ 调用成功: {response[:100]}...')
    except Exception as e:
        print(f'   ❌ 调用失败: {str(e)}')
        return False

    print('\n' + '=' * 60)
    print('🎉 智谱AI集成测试通过!')
    return True

def test_config_templates():
    """测试配置模板"""
    print('\n📋 测试配置模板...')
    print('=' * 60)
    
    templates = ["unified", "ai_enhanced", "dashscope", "deepseek", "zhipuai", "traditional"]
    
    for template_name in templates:
        try:
            config = get_config_template(template_name)
            ai_enabled = config.get("ai_analysis_config", {}).get("enabled", False)
            llm_config = config.get("llm_service_config", {})
            default_provider = llm_config.get("default_provider", "none")
            
            print(f'✅ {template_name:12}: AI={"启用" if ai_enabled else "禁用"}, 默认提供商={default_provider}')
        except Exception as e:
            print(f'❌ {template_name:12}: 错误 - {e}')

if __name__ == "__main__":
    print("🚀 智谱AI集成测试")
    print("=" * 60)
    
    # 测试配置模板
    test_config_templates()
    
    # 测试智谱AI集成
    success = test_zhipuai_setup()
    
    if success:
        print("\n🎉 所有测试通过! 智谱AI已成功集成到系统中。")
        print("\n📝 使用方法:")
        print("   1. 在代码中使用配置:")
        print("      from crypto_trading_agents.config.ai_analysis_config import get_config_template")
        print("      config = get_config_template('zhipuai')")
        print("   2. 或者设置环境变量后直接使用:")
        print("      export ZHIPUAI_API_KEY='your_api_key'")
    else:
        print("\n❌ 测试失败，请检查配置和网络连接。")
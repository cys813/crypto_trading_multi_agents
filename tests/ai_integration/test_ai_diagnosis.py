#!/usr/bin/env python3
"""
诊断AI分析功能为什么没有工作
"""
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from crypto_trading_agents.default_config import DEFAULT_CONFIG
from crypto_trading_agents.unified_config import get_unified_config
from crypto_trading_agents.services.llm_service import llm_service, is_llm_service_available
from crypto_trading_agents.agents.analysts.sentiment_analyst import SentimentAnalyst
import json

def diagnose_ai_setup():
    """诊断AI设置"""
    print("🔍 诊断AI分析功能设置...")
    print("=" * 60)
    
    # 1. 检查环境变量
    print("1. 环境变量检查:")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"   DASHSCOPE_API_KEY: {'✅ 已设置' if dashscope_key else '❌ 未设置'}")
    print(f"   DEEPSEEK_API_KEY: {'✅ 已设置' if deepseek_key else '❌ 未设置'}")
    print(f"   OPENAI_API_KEY: {'✅ 已设置' if openai_key else '❌ 未设置'}")
    
    # 2. 检查LLM服务状态
    print("\n2. LLM服务状态:")
    print(f"   LLM服务可用性: {'✅ 可用' if is_llm_service_available() else '❌ 不可用'}")
    print(f"   已初始化适配器数: {len(llm_service.llm_adapters)}")
    if llm_service.llm_adapters:
        print(f"   可用适配器: {list(llm_service.llm_adapters.keys())}")
        print(f"   默认提供者: {llm_service.default_provider}")
    
    # 3. 检查配置
    print("\n3. 配置检查:")
    # 获取统一配置
    unified_config = get_unified_config()
    print(f"   统一配置AI启用: {unified_config.get('ai_analysis_config', {}).get('enabled', False)}")
    
    # 检查默认配置中的LLM相关设置
    llm_provider = DEFAULT_CONFIG.get("llm_provider", "未设置")
    deep_think_llm = DEFAULT_CONFIG.get("deep_think_llm", "未设置")
    quick_think_llm = DEFAULT_CONFIG.get("quick_think_llm", "未设置")
    print(f"   LLM提供者: {llm_provider}")
    print(f"   深度思考模型: {deep_think_llm}")
    print(f"   快速思考模型: {quick_think_llm}")
    
    # 4. 测试SentimentAnalyst的AI状态
    print("\n4. SentimentAnalyst AI状态:")
    config = DEFAULT_CONFIG.copy()
    # 合并AI配置
    config.update(unified_config)
    
    analyst = SentimentAnalyst(config)
    print(f"   AI启用状态: {'✅ 启用' if analyst.is_ai_enabled() else '❌ 禁用'}")
    print(f"   LLM服务可用: {'✅ 可用' if is_llm_service_available() else '❌ 不可用'}")
    
    # 5. 尝试初始化LLM服务
    print("\n5. LLM服务初始化测试:")
    llm_service_config = unified_config.get("llm_service_config")
    if llm_service_config:
        print("   尝试初始化LLM服务...")
        try:
            from crypto_trading_agents.services.llm_service import initialize_llm_service
            success = initialize_llm_service(llm_service_config)
            print(f"   初始化结果: {'✅ 成功' if success else '❌ 失败'}")
            print(f"   初始化后适配器数: {len(llm_service.llm_adapters)}")
            if llm_service.llm_adapters:
                print(f"   初始化后可用适配器: {list(llm_service.llm_adapters.keys())}")
        except Exception as e:
            print(f"   初始化失败: {str(e)}")
    else:
        print("   未找到LLM服务配置")
    
    # 6. 测试简单的LLM调用
    print("\n6. LLM调用测试:")
    if is_llm_service_available() and llm_service.llm_adapters:
        try:
            print("   发送简单测试请求...")
            response = llm_service.call_llm("请用一个词回答：比特币的前景如何？", 
                                          temperature=0.1, max_tokens=50)
            print(f"   ✅ 调用成功: {response[:100]}...")
        except Exception as e:
            print(f"   ❌ 调用失败: {str(e)}")
    else:
        print("   ⚠️  LLM服务不可用，跳过测试")
    
    print("\n" + "=" * 60)
    print("诊断完成")

def test_sentiment_analyst_with_ai():
    """测试SentimentAnalyst的AI功能"""
    print("\n🧪 测试SentimentAnalyst AI功能...")
    print("=" * 60)
    
    # 获取配置并启用AI
    config = DEFAULT_CONFIG.copy()
    ai_config = get_unified_config()
    config.update(ai_config)
    
    # 强制启用AI
    config["ai_analysis_config"]["enabled"] = True
    
    analyst = SentimentAnalyst(config)
    
    print(f"AI启用状态: {analyst.is_ai_enabled()}")
    print(f"LLM服务可用: {is_llm_service_available()}")
    
    # 获取AI分析信息
    ai_info = analyst.get_ai_analysis_info()
    print(f"AI分析信息: {json.dumps(ai_info, ensure_ascii=False, indent=2)}")
    
    print("=" * 60)

if __name__ == "__main__":
    diagnose_ai_setup()
    test_sentiment_analyst_with_ai()
#!/usr/bin/env python3
"""
测试直接配置的智谱AI集成
不使用环境变量，直接在配置中指定API密钥
"""
import sys
import os
sys.path.insert(0, './src')

from crypto_trading_agents.config.ai_analysis_config import get_config_template, get_zhipuai_direct_config
from crypto_trading_agents.services.llm_service import llm_service, initialize_llm_service, is_llm_service_available
from crypto_trading_agents.agents.analysts.sentiment_analyst import SentimentAnalyst
import json

def test_direct_zhipuai_setup():
    """测试直接配置的智谱AI设置"""
    print('🔍 测试直接配置的智谱AI集成...')
    print('=' * 60)

    # 1. 获取直接配置的智谱AI配置
    print('1. 获取直接配置的智谱AI配置:')
    config = get_zhipuai_direct_config()
    llm_config = config.get('llm_service_config', {})
    providers = llm_config.get('providers', {})
    zhipuai_config = providers.get('zhipuai', {})
    
    print(f'   默认提供商: {llm_config.get("default_provider", "未设置")}')
    print(f'   模型: {zhipuai_config.get("model", "未设置")}')
    print(f'   API密钥: {"✅ 已配置" if zhipuai_config.get("api_key") else "❌ 未配置"}')
    print(f'   API密钥值: {zhipuai_config.get("api_key", "")[:20]}...')

    # 2. 初始化LLM服务
    print('\n2. 初始化LLM服务:')
    success = initialize_llm_service(llm_config)
    print(f'   初始化结果: {"✅ 成功" if success else "❌ 失败"}')
    
    if not success:
        print('   ❌ LLM服务初始化失败')
        return False

    # 3. 检查服务状态
    print('\n3. LLM服务状态:')
    available = is_llm_service_available()
    print(f'   服务可用性: {"✅ 可用" if available else "❌ 不可用"}')
    print(f'   可用适配器数: {len(llm_service.llm_adapters)}')
    
    if llm_service.llm_adapters:
        print(f'   可用适配器: {list(llm_service.llm_adapters.keys())}')
        print(f'   默认提供商: {llm_service.default_provider}')
    else:
        print('   ❌ 没有可用的LLM适配器')
        return False

    # 4. 测试简单的LLM调用
    print('\n4. LLM调用测试:')
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
    print('🎉 直接配置的智谱AI集成测试通过!')
    return True

def test_template_based_config():
    """测试基于模板的配置"""
    print('\n📋 测试基于模板的配置...')
    print('=' * 60)
    
    # 测试zhipuai_direct模板
    try:
        config = get_config_template("zhipuai_direct")
        ai_enabled = config.get("ai_analysis_config", {}).get("enabled", False)
        llm_config = config.get("llm_service_config", {})
        default_provider = llm_config.get("default_provider", "none")
        providers = llm_config.get("providers", {})
        zhipuai_info = providers.get("zhipuai", {})
        api_key = zhipuai_info.get("api_key", "")
        
        print(f'✅ zhipuai_direct模板:')
        print(f'   AI启用: {"是" if ai_enabled else "否"}')
        print(f'   默认提供商: {default_provider}')
        print(f'   API密钥: {"✅ 已配置" if api_key else "❌ 未配置"}')
        print(f'   API密钥值: {api_key[:20]}...')
        
        return True
        
    except Exception as e:
        print(f'❌ zhipuai_direct模板测试失败: {e}')
        return False

def test_sentiment_analyst_with_direct_config():
    """测试使用直接配置的情绪分析师"""
    print('\n🤖 测试使用直接配置的情绪分析师...')
    print('=' * 60)
    
    try:
        # 获取直接配置
        config = get_zhipuai_direct_config()
        
        # 创建情绪分析师
        analyst = SentimentAnalyst(config)
        
        print(f'   AI启用状态: {"✅ 启用" if analyst.is_ai_enabled() else "❌ 禁用"}')
        print(f'   LLM服务可用: {"✅ 可用" if analyst.ai_enabled else "❌ 不可用"}')
        
        # 准备测试数据
        test_data = {
            "twitter_sentiment": {
                "sentiment_score": 0.65,
                "engagement_rate": 0.035,
                "spam_ratio": 0.05,
                "total_tweets": 1250,
                "positive_tweets": 450,
                "negative_tweets": 200,
                "neutral_tweets": 600
            },
            "reddit_sentiment": {
                "sentiment_score": 0.58,
                "engagement_rate": 0.028,
                "upvote_ratio": 0.72,
                "total_posts": 340,
                "positive_posts": 150,
                "negative_posts": 80,
                "neutral_posts": 110
            },
            "fear_greed_index": {
                "fear_greed_value": 65,
                "classification": "Greed",
                "weekly_change": 8,
                "monthly_change": 12,
                "yearly_change": -5
            },
            "timestamp": "2025-08-07T15:30:00Z"
        }
        
        # 执行分析
        print('\n   执行情绪分析测试...')
        result = analyst.analyze(test_data)
        
        print(f'   ✅ 分析完成!')
        print(f'   AI增强: {"✅ 是" if result.get("ai_enhanced", False) else "❌ 否"}')
        
        if "traditional_analysis" in result:
            traditional = result["traditional_analysis"]
            print(f'   传统分析置信度: {traditional.get("confidence", 0):.3f}')
            
        return True
        
    except Exception as e:
        print(f'   ❌ 情绪分析师测试失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 直接配置的智谱AI集成测试")
    print("=" * 60)
    
    # 测试基于模板的配置
    template_success = test_template_based_config()
    
    # 测试直接配置的智谱AI设置
    direct_success = test_direct_zhipuai_setup()
    
    # 测试情绪分析师
    analyst_success = test_sentiment_analyst_with_direct_config()
    
    print("\n" + "=" * 60)
    print("📋 测试总结:")
    print(f"   模板配置测试: {'✅ 通过' if template_success else '❌ 失败'}")
    print(f"   直接配置测试: {'✅ 通过' if direct_success else '❌ 失败'}")
    print(f"   情绪分析师测试: {'✅ 通过' if analyst_success else '❌ 失败'}")
    
    if template_success and direct_success and analyst_success:
        print("\n🎉 所有测试通过! 直接配置的智谱AI已成功集成到系统中。")
        print("\n📝 使用方法:")
        print("   1. 在代码中使用配置:")
        print("      from crypto_trading_agents.config.ai_analysis_config import get_config_template")
        print("      config = get_config_template('zhipuai_direct')")
        print("   2. 或者直接使用函数:")
        print("      from crypto_trading_agents.config.zhipuai_direct_config import get_zhipuai_direct_config")
        print("      config = get_zhipuai_direct_config()")
    else:
        print("\n❌ 部分测试失败，请检查配置和网络连接。")
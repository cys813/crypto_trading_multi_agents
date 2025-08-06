#!/usr/bin/env python3
"""
测试AI增强技术分析功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
sys.path.insert(0, project_root)

from crypto_trading_agents.agents.analysts.technical_analyst import TechnicalAnalyst
from crypto_trading_agents.config.ai_analysis_config import get_config_template

def test_traditional_analysis():
    """测试传统技术分析"""
    print("\n🔧 测试传统技术分析")
    print("=" * 60)
    
    try:
        # 使用传统分析配置
        config = get_config_template("traditional")
        analyst = TechnicalAnalyst(config)
        
        # 模拟技术分析数据
        test_data = {
            "symbol": "BTC/USDT",
            "data_source": "mock",
            "indicators": {
                "rsi": {"value": 65.5, "signal": "neutral"},
                "macd": {"macd": 125.3, "signal": 98.7, "histogram": 26.6, "signal": "bullish"},
                "bollinger_bands": {
                    "upper": 52000,
                    "middle": 50000,
                    "lower": 48000,
                    "position": "middle",
                    "signal": "neutral"
                },
                "stochastic": {"k": 75.2, "d": 68.9, "signal": "overbought"},
                "williams_r": {"value": -25.3, "signal": "neutral"}
            },
            "market_structure": {
                "trend": "uptrend",
                "higher_highs": True,
                "higher_lows": True
            },
            "volume_profile": {
                "volume_trend": "increasing",
                "buying_pressure": "moderate"
            },
            "ohlcv_data": [
                {"open": 49500, "high": 50500, "low": 49000, "close": 50000, "volume": 1000000}
            ]
        }
        
        # 执行分析
        result = analyst.analyze(test_data)
        
        print("✅ 传统技术分析完成")
        print(f"📊 分析类型: {result.get('analysis_type', 'unknown')}")
        print(f"🤖 AI增强: {result.get('ai_enhanced', False)}")
        print(f"📈 主要信号: {len(result.get('signals', {}).get('bullish_signals', []))} 看涨, {len(result.get('signals', {}).get('bearish_signals', []))} 看跌")
        print(f"🎯 置信度: {result.get('confidence', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 传统技术分析测试失败: {e}")
        return False

def test_ai_enhanced_analysis():
    """测试AI增强技术分析"""
    print("\n🤖 测试AI增强技术分析")
    print("=" * 60)
    
    # 检查是否有API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("⚠️  未找到DASHSCOPE_API_KEY，跳过AI增强测试")
        return False
    
    try:
        # 使用AI增强配置
        config = get_config_template("dashscope")
        analyst = TechnicalAnalyst(config)
        
        # 模拟更复杂的技术分析数据
        test_data = {
            "symbol": "BTC/USDT",
            "data_source": "binance",
            "indicators": {
                "rsi": {"value": 72.3, "signal": "overbought"},
                "macd": {"macd": -45.7, "signal": -20.1, "histogram": -25.6, "signal": "bearish"},
                "bollinger_bands": {
                    "upper": 52000,
                    "middle": 50000,
                    "lower": 48000,
                    "position": "upper",
                    "signal": "overbought"
                },
                "stochastic": {"k": 85.4, "d": 78.9, "signal": "overbought"},
                "williams_r": {"value": -15.7, "signal": "overbought"}
            },
            "market_structure": {
                "trend": "uptrend",
                "higher_highs": True,
                "higher_lows": False,
                "pattern": "rising_wedge",
                "breakout_potential": "high"
            },
            "volume_profile": {
                "volume_trend": "decreasing",
                "buying_pressure": "low",
                "selling_pressure": "high",
                "volume_spike": False
            },
            "ohlcv_data": [
                {"open": 49000, "high": 51500, "low": 48500, "close": 51200, "volume": 800000},
                {"open": 51200, "high": 52000, "low": 50800, "close": 51800, "volume": 750000},
                {"open": 51800, "high": 52500, "low": 51500, "close": 52200, "volume": 600000}
            ]
        }
        
        print("🔄 开始AI增强分析...")
        result = analyst.analyze(test_data)
        
        print("✅ AI增强技术分析完成")
        print(f"📊 分析类型: {result.get('analysis_type', 'unknown')}")
        print(f"🤖 AI增强: {result.get('ai_enhanced', False)}")
        
        if result.get('ai_enhanced'):
            ai_analysis = result.get('ai_analysis', {})
            combined_insights = result.get('combined_insights', {})
            final_recommendation = result.get('final_recommendation', {})
            
            print(f"🎯 AI置信度: {ai_analysis.get('confidence_score', 0):.2f}")
            print(f"📈 AI趋势判断: {ai_analysis.get('trend_analysis', {}).get('overall_direction', 'unknown')}")
            print(f"💡 最终建议: {final_recommendation.get('action', 'unknown')}")
            print(f"⚖️  综合置信度: {combined_insights.get('confidence', {}).get('combined', 0):.2f}")
            
            # 输出AI分析摘要
            if ai_analysis.get('analysis_summary'):
                print(f"\n📋 AI分析摘要:")
                print(ai_analysis['analysis_summary'][:200] + "..." if len(ai_analysis['analysis_summary']) > 200 else ai_analysis['analysis_summary'])
        
        if result.get('ai_error'):
            print(f"⚠️  AI分析错误: {result['ai_error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI增强技术分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_templates():
    """测试配置模板"""
    print("\n⚙️  测试配置模板")
    print("=" * 60)
    
    templates = ["traditional", "dashscope", "deepseek", "ai_enhanced"]
    
    for template_name in templates:
        try:
            config = get_config_template(template_name)
            ai_enabled = config.get("ai_analysis_config", {}).get("enabled", False)
            provider = config.get("llm_config", {}).get("provider", "none")
            
            print(f"✅ {template_name}: AI={'启用' if ai_enabled else '禁用'}, 提供商={provider}")
            
        except Exception as e:
            print(f"❌ {template_name}: 配置失败 - {e}")
    
    return True

def main():
    """主测试函数"""
    print("🔍 AI增强技术分析测试")
    print("=" * 70)
    print("💡 测试目标:")
    print("   - 验证传统技术分析功能")
    print("   - 测试AI增强分析集成")
    print("   - 检查配置模板")
    print("   - 验证错误处理机制")
    print("=" * 70)
    
    # 运行所有测试
    tests = [
        ("配置模板测试", test_config_templates),
        ("传统技术分析", test_traditional_analysis),
        ("AI增强技术分析", test_ai_enhanced_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n📋 AI增强技术分析测试总结")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    print("\n💡 使用说明:")
    print("   1. 设置环境变量 DASHSCOPE_API_KEY 或 DEEPSEEK_API_KEY")
    print("   2. 选择配置模板: traditional, dashscope, deepseek, ai_enhanced")
    print("   3. 初始化 TechnicalAnalyst(config)")
    print("   4. 调用 analyst.analyze(data) 进行分析")
    
    print("\n🔧 配置示例:")
    print("   export DASHSCOPE_API_KEY='your_api_key_here'")
    print("   config = get_config_template('dashscope')")
    print("   analyst = TechnicalAnalyst(config)")
    
    if passed == total:
        print("\n🎉 所有测试通过！AI增强技术分析功能已就绪")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查配置和依赖")


if __name__ == "__main__":
    main()
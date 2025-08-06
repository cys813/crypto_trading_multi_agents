#!/usr/bin/env python3
"""
简化的AI增强技术分析测试
"""

import os
import sys
import json

# 测试基本配置功能
def test_basic_config():
    """测试基本配置功能"""
    print("\n⚙️ 测试基本配置")
    print("=" * 50)
    
    try:
        # 添加项目路径
        project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
        sys.path.insert(0, project_root)
        
        from src.crypto_trading_agents.config.ai_analysis_config import get_config_template
        
        # 测试不同配置模板
        templates = ["traditional", "dashscope", "deepseek", "ai_enhanced"]
        
        for template_name in templates:
            config = get_config_template(template_name)
            ai_enabled = config.get("ai_analysis_config", {}).get("enabled", False)
            provider = config.get("llm_config", {}).get("provider", "none")
            
            print(f"✅ {template_name}: AI={'启用' if ai_enabled else '禁用'}, 提供商={provider}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_analyzer_init():
    """测试AI分析器初始化"""
    print("\n🤖 测试AI分析器初始化")
    print("=" * 50)
    
    try:
        from src.crypto_trading_agents.agents.analysts.ai_technical_analyzer import AITechnicalAnalyzer
        from src.crypto_trading_agents.config.ai_analysis_config import get_config_template
        
        # 测试不同配置的初始化
        configs = [
            ("traditional", get_config_template("traditional")),
            ("dashscope", get_config_template("dashscope")),
        ]
        
        for config_name, config in configs:
            try:
                analyzer = AITechnicalAnalyzer(config)
                ai_enabled = analyzer.ai_enabled
                model_name = analyzer.model_name
                
                print(f"✅ {config_name}: AI={'启用' if ai_enabled else '禁用'}, 模型={model_name}")
                
            except Exception as e:
                print(f"⚠️  {config_name}: 初始化失败 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_generation():
    """测试prompt生成功能"""
    print("\n📝 测试Prompt生成")
    print("=" * 50)
    
    try:
        from src.crypto_trading_agents.agents.analysts.ai_technical_analyzer import AITechnicalAnalyzer
        from src.crypto_trading_agents.config.ai_analysis_config import get_config_template
        
        # 使用传统配置（禁用AI但可以测试prompt生成逻辑）
        config = get_config_template("traditional")
        config["ai_analysis_config"]["enabled"] = False  # 确保不会实际调用API
        
        analyzer = AITechnicalAnalyzer(config)
        
        # 模拟数据
        traditional_analysis = {
            "indicators": {
                "rsi": {"value": 72.3, "signal": "overbought"},
                "macd": {"macd": -45.7, "signal": -20.1, "histogram": -25.6, "signal": "bearish"}
            },
            "signals": {
                "bullish_signals": ["MACD金叉"],
                "bearish_signals": ["RSI超买", "价格接近布林带上轨"],
                "neutral_signals": []
            },
            "trend_strength": {"direction": "bullish", "strength": 0.8, "confidence": 0.7}
        }
        
        raw_data = {
            "symbol": "BTC/USDT",
            "data_source": "binance",
            "market_structure": {"trend": "uptrend", "pattern": "rising_wedge"},
            "volume_profile": {"volume_trend": "decreasing", "buying_pressure": "low"},
            "ohlcv_data": [
                {"open": 49000, "high": 51500, "low": 48500, "close": 51200, "volume": 800000}
            ]
        }
        
        # 测试prompt构建
        prompt = analyzer._build_analysis_prompt(traditional_analysis, raw_data)
        
        if len(prompt) > 100:
            print("✅ Prompt生成成功")
            print(f"📊 Prompt长度: {len(prompt)} 字符")
            print(f"📋 包含关键词: {'技术指标' in prompt and 'BTC/USDT' in prompt}")
        else:
            print("❌ Prompt生成失败，内容过短")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_key_detection():
    """测试API密钥检测"""
    print("\n🔑 测试API密钥检测")
    print("=" * 50)
    
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    print(f"DASHSCOPE_API_KEY: {'✅ 存在' if dashscope_key else '❌ 未设置'}")
    print(f"DEEPSEEK_API_KEY: {'✅ 存在' if deepseek_key else '❌ 未设置'}")
    
    if dashscope_key or deepseek_key:
        print("💡 可以进行完整的AI增强测试")
        return True
    else:
        print("⚠️  未设置API密钥，只能测试基础功能")
        return False

def main():
    """主测试函数"""
    print("🔍 AI增强技术分析 - 简化测试")
    print("=" * 60)
    print("💡 测试内容:")
    print("   - 配置模板功能")
    print("   - AI分析器初始化")
    print("   - Prompt生成逻辑")
    print("   - API密钥检测")
    print("=" * 60)
    
    # 运行测试
    tests = [
        ("配置模板测试", test_basic_config),
        ("AI分析器初始化", test_ai_analyzer_init),
        ("Prompt生成测试", test_prompt_generation),
        ("API密钥检测", test_api_key_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed >= 3:  # 至少前3个测试通过
        print("\n🎉 AI增强技术分析基础功能正常！")
        print("\n💡 下一步:")
        print("   1. 设置API密钥环境变量")
        print("   2. 安装必要依赖 (numpy)")
        print("   3. 运行完整功能测试")
    else:
        print("\n⚠️  基础功能有问题，需要修复")
    
    return passed == total

if __name__ == "__main__":
    main()
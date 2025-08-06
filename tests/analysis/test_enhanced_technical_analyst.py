#!/usr/bin/env python3
"""
测试增强版技术分析师功能
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_technical_analyst():
    """测试技术分析师功能"""
    print("测试增强版技术分析师...")
    
    try:
        # 导入技术分析师
        from crypto_trading_agents.crypto_trading_agents.agents.analysts.technical_analyst import TechnicalAnalyst
        
        # 创建测试配置
        config = {
            "analysis_config": {
                "technical_indicators": ["rsi", "macd", "bollinger_bands", "stochastic"]
            },
            "layered_data_config": {
                "enabled": True
            },
            "ai_analysis_config": {
                "enabled": True
            },
            "llm_service_config": {
                "providers": {
                    "dashscope": {
                        "model": "qwen-plus",
                        "api_key": "test_key"
                    }
                }
            }
        }
        
        # 创建技术分析师实例
        analyst = TechnicalAnalyst(config)
        
        print("✅ 技术分析师初始化成功")
        
        # 测试数据收集
        print("\n测试数据收集功能...")
        symbol = "BTC/USDT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        data = analyst.collect_data(symbol, end_date)
        
        if "error" in data:
            print(f"❌ 数据收集失败: {data['error']}")
            return False
        
        print(f"✅ 数据收集成功，数据源: {data.get('data_source', 'unknown')}")
        
        # 检查分层数据
        if "layered_data" in data:
            layered_data = data["layered_data"]
            layers = layered_data.get("layers", {})
            print(f"✅ 分层数据获取成功，包含 {len(layers)} 层数据")
            
            for layer_name, layer_info in layers.items():
                data_count = len(layer_info.get("data", []))
                timeframe = layer_info.get("timeframe", "unknown")
                print(f"   - {layer_name}: {data_count} 个数据点, 时间框架: {timeframe}")
        
        # 测试技术分析
        print("\n测试技术分析功能...")
        analysis_result = analyst.analyze(data)
        
        if "error" in analysis_result:
            print(f"❌ 技术分析失败: {analysis_result['error']}")
            return False
        
        print("✅ 技术分析成功")
        
        # 显示分析结果摘要
        print("\n分析结果摘要:")
        print(f" - 分析类型: {analysis_result.get('analysis_type', 'unknown')}")
        print(f" - AI增强: {analysis_result.get('ai_enhanced', False)}")
        print(f" - 市场状态: {analysis_result.get('market_regime', 'unknown')}")
        print(f" - 置信度: {analysis_result.get('confidence', 0):.2f}")
        
        # 显示技术指标
        indicators = analysis_result.get("indicators", {})
        if indicators:
            print(f"\n技术指标:")
            for layer_name, layer_indicators in indicators.items():
                if isinstance(layer_indicators, dict):
                    print(f" - {layer_name}:")
                    for key, value in layer_indicators.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.2f}")
                        else:
                            print(f"   {key}: {value}")
        
        # 显示关键观察
        observations = analysis_result.get("key_observations", [])
        if observations:
            print(f"\n关键观察:")
            for obs in observations[:3]:  # 显示前3个观察
                print(f" - {obs}")
        
        # 测试AI增强分析（如果启用）
        if analysis_result.get("ai_enhanced", False):
            print(f"\nAI增强分析:")
            ai_analysis = analysis_result.get("ai_analysis", {})
            if ai_analysis:
                print("✅ AI分析成功")
                confidence = ai_analysis.get("confidence_level", 0)
                print(f" - AI置信度: {confidence:.2f}")
                
                insights = ai_analysis.get("key_insights", [])
                if insights:
                    print(" - AI洞察:")
                    for insight in insights[:2]:
                        print(f"   * {insight}")
        
        print("\n✅ 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_layered_indicators():
    """测试分层技术指标计算"""
    print("\n测试分层技术指标计算...")
    
    try:
        from crypto_trading_agents.crypto_trading_agents.agents.analysts.technical_analyst import TechnicalAnalyst
        
        config = {
            "layered_data_config": {"enabled": True}
        }
        
        analyst = TechnicalAnalyst(config)
        
        # 创建模拟分层数据
        mock_layered_data = {
            "layers": {
                "layer_1": {
                    "data": [
                        [1640995200000, 47000, 47500, 46800, 47200, 1000],
                        [1640995600000, 47200, 47800, 47000, 47600, 1200],
                        [1640996000000, 47600, 48000, 47400, 47800, 1100]
                    ]
                },
                "layer_2": {
                    "data": [
                        [1640995200000, 47000, 47500, 46800, 47200, 1000],
                        [1640995600000, 47200, 47800, 47000, 47600, 1200],
                        [1640996000000, 47600, 48000, 47400, 47800, 1100]
                    ]
                }
            }
        }
        
        # 测试分层指标计算
        indicators = analyst._calculate_layered_indicators(mock_layered_data)
        
        print(f"✅ 分层指标计算成功")
        print(f" - 计算了 {len(indicators)} 个指标组")
        
        for layer_name, layer_indicators in indicators.items():
            print(f" - {layer_name}: {list(layer_indicators.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分层指标测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试增强版技术分析师...")
    
    # 基本功能测试
    test1_success = test_technical_analyst()
    
    # 分层指标测试
    test2_success = test_layered_indicators()
    
    # 总结
    print(f"\n测试总结:")
    print(f" - 技术分析师基本功能: {'✅ 通过' if test1_success else '❌ 失败'}")
    print(f" - 分层技术指标计算: {'✅ 通过' if test2_success else '❌ 失败'}")
    
    if test1_success and test2_success:
        print("\n🎉 所有测试通过! 技术分析师修改成功!")
    else:
        print("\n⚠️  部分测试失败，请检查相关功能")
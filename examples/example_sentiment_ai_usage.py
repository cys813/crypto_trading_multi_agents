#!/usr/bin/env python3
"""
SentimentAnalyst AI增强使用示例

演示如何使用集成了AI功能的情绪分析师
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from crypto_trading_agents.crypto_trading_agents.config.ai_analysis_config import get_config_template

def example_traditional_sentiment_analysis():
    """传统情绪分析示例"""
    print("📊 传统情绪分析示例")
    print("=" * 40)
    
    # 使用传统分析配置
    config = get_config_template("traditional")
    
    print("配置信息:")
    print(f"- AI启用: {config.get('ai_analysis_config', {}).get('enabled', False)}")
    print(f"- 情绪源: {config.get('analysis_config', {}).get('sentiment_sources', [])}")
    
    # 这里演示配置的使用，实际使用时需要导入SentimentAnalyst
    print("\n传统分析流程:")
    print("1. 收集Twitter、Reddit、新闻等情绪数据")
    print("2. 计算各平台情绪得分")
    print("3. 综合分析整体市场情绪")
    print("4. 生成情绪报告和信号")

def example_ai_enhanced_sentiment_analysis():
    """AI增强情绪分析示例"""
    print("\n🤖 AI增强情绪分析示例")
    print("=" * 40)
    
    # 使用AI增强配置
    config = get_config_template("ai_enhanced")
    
    print("配置信息:")
    print(f"- AI启用: {config.get('ai_analysis_config', {}).get('enabled', True)}")
    print(f"- LLM提供商: {config.get('llm_config', {}).get('provider', 'unknown')}")
    print(f"- 模型: {config.get('llm_config', {}).get('model', 'unknown')}")
    print(f"- 温度: {config.get('ai_analysis_config', {}).get('temperature', 0.1)}")
    print(f"- 最大tokens: {config.get('ai_analysis_config', {}).get('max_tokens', 3000)}")
    
    print("\nAI增强分析流程:")
    print("1. 执行传统情绪分析")
    print("2. 构建专业化AI分析prompt")
    print("3. 调用LLM进行深度情绪解读")
    print("4. 融合传统分析和AI洞察")
    print("5. 生成增强的情绪报告")

def example_ai_analysis_result():
    """AI分析结果示例"""
    print("\n📈 AI增强分析结果示例")
    print("=" * 40)
    
    # 模拟AI增强分析结果
    enhanced_result = {
        "traditional_analysis": {
            "overall_sentiment": {
                "sentiment": "bullish",
                "score": 0.72,
                "strength": "strong"
            },
            "key_signals": [
                "Twitter情绪看涨",
                "Reddit社区质量高",
                "机构关注度提升"
            ],
            "confidence": 0.78
        },
        "ai_analysis": {
            "sentiment_forecast": {
                "next_3_days": "看涨",
                "next_7_days": "中性",
                "turning_point_probability": 0.25
            },
            "market_psychology_cycle": {
                "current_phase": "乐观",
                "phase_confidence": 0.82,
                "next_phase_prediction": "可能转向贪婪"
            },
            "anomaly_signals": {
                "detected_anomalies": ["社交量异常增长"],
                "price_sentiment_divergence": "轻微",
                "manipulation_risk": 0.15
            },
            "trading_psychology": {
                "crowd_behavior": "乐观但理性",
                "fomo_level": 0.3,
                "panic_selling_risk": 0.05
            },
            "contrarian_analysis": {
                "contrarian_signal_strength": 0.2,
                "over_optimism_level": 0.35,
                "contrarian_opportunity": "弱"
            },
            "investment_recommendation": {
                "sentiment_based_action": "适度买入",
                "key_monitoring_metrics": [
                    "恐惧贪婪指数",
                    "社交媒体提及量",
                    "意见领袖情绪"
                ],
                "entry_signals": [
                    "恐惧贪婪指数回落至65以下",
                    "Reddit社区讨论深度增加"
                ]
            },
            "confidence_assessment": {
                "analysis_confidence": 0.85,
                "prediction_reliability": "高"
            },
            "executive_summary": "当前市场情绪整体乐观，短期看涨趋势明显，但需注意避免过度乐观。建议适度买入，密切关注恐惧贪婪指数变化。"
        },
        "enhanced_insights": {
            "sentiment_consensus": {
                "traditional": "bullish",
                "ai_forecast": "看涨",
                "agreement": True
            },
            "confidence_assessment": {
                "combined": 0.87,
                "reliability": "高"
            },
            "market_psychology": {
                "current_phase": "乐观",
                "phase_confidence": 0.82
            }
        },
        "final_assessment": {
            "overall_recommendation": "buy",
            "confidence": 0.87,
            "executive_summary": "AI增强分析显示市场情绪乐观，建议适度买入"
        }
    }
    
    # 显示分析结果
    print("📊 传统分析结果:")
    traditional = enhanced_result["traditional_analysis"]
    print(f"- 整体情绪: {traditional['overall_sentiment']['sentiment']}")
    print(f"- 情绪强度: {traditional['overall_sentiment']['strength']}")
    print(f"- 置信度: {traditional['confidence']:.2f}")
    
    print("\n🤖 AI增强洞察:")
    ai_analysis = enhanced_result["ai_analysis"]
    print(f"- 3天预测: {ai_analysis['sentiment_forecast']['next_3_days']}")
    print(f"- 市场心理: {ai_analysis['market_psychology_cycle']['current_phase']}")
    print(f"- 投资建议: {ai_analysis['investment_recommendation']['sentiment_based_action']}")
    print(f"- AI置信度: {ai_analysis['confidence_assessment']['analysis_confidence']:.2f}")
    
    print("\n🎯 最终评估:")
    final = enhanced_result["final_assessment"]
    print(f"- 综合建议: {final['overall_recommendation']}")
    print(f"- 综合置信度: {final['confidence']:.2f}")
    print(f"- 执行摘要: {final['executive_summary']}")

def example_different_llm_configs():
    """不同LLM配置示例"""
    print("\n⚙️ 不同LLM配置示例")
    print("=" * 40)
    
    configs = [
        ("DashScope (阿里百炼)", "dashscope"),
        ("DeepSeek", "deepseek"),
        ("传统分析", "traditional")
    ]
    
    for name, template in configs:
        config = get_config_template(template)
        ai_enabled = config.get("ai_analysis_config", {}).get("enabled", False)
        provider = config.get("llm_config", {}).get("provider", "N/A")
        model = config.get("llm_config", {}).get("model", "N/A")
        
        print(f"\n{name}:")
        print(f"  - AI启用: {ai_enabled}")
        if ai_enabled:
            print(f"  - 提供商: {provider}")
            print(f"  - 模型: {model}")
        else:
            print(f"  - 使用传统分析方法")

def example_api_key_setup():
    """API密钥设置示例"""
    print("\n🔑 API密钥设置示例")
    print("=" * 40)
    
    print("环境变量设置:")
    print("# 阿里百炼")
    print("export DASHSCOPE_API_KEY='your_dashscope_api_key'")
    print()
    print("# DeepSeek")
    print("export DEEPSEEK_API_KEY='your_deepseek_api_key'")
    print()
    
    print("当前环境变量状态:")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    print(f"- DASHSCOPE_API_KEY: {'已设置' if dashscope_key else '未设置'}")
    print(f"- DEEPSEEK_API_KEY: {'已设置' if deepseek_key else '未设置'}")
    
    if not dashscope_key and not deepseek_key:
        print("\n⚠️ 建议至少设置一个API密钥以启用AI功能")

def example_usage_scenarios():
    """使用场景示例"""
    print("\n📋 使用场景示例")
    print("=" * 40)
    
    scenarios = [
        {
            "场景": "快速情绪检查",
            "配置": "traditional",
            "描述": "只需要基础情绪分析，快速获取结果"
        },
        {
            "场景": "深度市场研究",
            "配置": "ai_enhanced",
            "描述": "需要深入的情绪洞察和预测分析"
        },
        {
            "场景": "自动化交易系统",
            "配置": "dashscope",
            "描述": "集成到自动化系统，需要稳定的AI分析"
        },
        {
            "场景": "研究报告生成",
            "配置": "deepseek",
            "描述": "生成详细的情绪分析报告"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n场景 {i}: {scenario['场景']}")
        print(f"  推荐配置: {scenario['配置']}")
        print(f"  使用说明: {scenario['描述']}")

if __name__ == "__main__":
    print("🚀 SentimentAnalyst AI增强功能使用指南")
    print("=" * 60)
    
    # 运行所有示例
    example_traditional_sentiment_analysis()
    example_ai_enhanced_sentiment_analysis()
    example_ai_analysis_result()
    example_different_llm_configs()
    example_api_key_setup()
    example_usage_scenarios()
    
    print("\n" + "=" * 60)
    print("✅ SentimentAnalyst AI增强功能演示完成!")
    print("\n📚 更多信息请参考:")
    print("- LLM_Integration_Plan.md - 完整集成计划")
    print("- test_sentiment_ai_simple.py - 功能测试")
    print("- ai_analysis_config.py - 配置选项")
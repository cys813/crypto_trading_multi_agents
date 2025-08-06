#!/usr/bin/env python3
"""
SentimentAnalyst AI集成测试脚本

测试SentimentAnalyst的AI增强功能
"""

import os
import sys
import json
from typing import Dict, Any
from unittest.mock import Mock, patch

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from crypto_trading_agents.agents.analysts.sentiment_analyst import SentimentAnalyst

def test_sentiment_analyst_ai_integration():
    """测试情绪分析师AI集成功能"""
    
    print("🧪 开始测试SentimentAnalyst AI集成...")
    
    # 测试配置
    config = {
        "llm_config": {
            "provider": "dashscope",
            "model": "qwen-plus",
            "api_key": "test_api_key"
        },
        "ai_analysis_config": {
            "enabled": True,
            "temperature": 0.1,
            "max_tokens": 3000
        },
        "analysis_config": {
            "sentiment_sources": ["twitter", "reddit", "news", "telegram"]
        }
    }
    
    # 创建分析师实例（AI暂时禁用以避免API调用）
    config["ai_analysis_config"]["enabled"] = False
    analyst = SentimentAnalyst(config)
    
    # 测试传统分析功能
    symbol = "BTC/USDT"
    end_date = "2024-01-15"
    
    print(f"📊 收集情绪数据: {symbol}")
    data = analyst.collect_data(symbol, end_date)
    
    if "error" in data:
        print(f"❌ 数据收集失败: {data['error']}")
        return False
    
    print("✅ 数据收集成功")
    print(f"- Twitter推文: {data.get('twitter_sentiment', {}).get('tweet_count', 'N/A'):,}")
    print(f"- Reddit帖子: {data.get('reddit_sentiment', {}).get('post_count', 'N/A'):,}")
    print(f"- 新闻文章: {data.get('news_sentiment', {}).get('article_count', 'N/A')}")
    print(f"- 恐惧贪婪指数: {data.get('fear_greed_index', {}).get('fear_greed_value', 'N/A')}")
    
    print(f"🔍 执行传统情绪分析...")
    traditional_result = analyst.analyze(data)
    
    if "error" in traditional_result:
        print(f"❌ 传统分析失败: {traditional_result['error']}")
        return False
    
    print("✅ 传统分析完成")
    overall_sentiment = traditional_result.get("overall_sentiment", {})
    print(f"- 整体情绪: {overall_sentiment.get('sentiment', 'unknown')}")
    print(f"- 情绪强度: {overall_sentiment.get('strength', 'unknown')}")
    print(f"- 置信度: {traditional_result.get('confidence', 0):.2f}")
    
    # 测试AI集成初始化
    print(f"🤖 测试AI适配器初始化...")
    
    # 重现配置启用AI
    config["ai_analysis_config"]["enabled"] = True
    
    # 模拟LLM适配器
    mock_llm_adapter = Mock()
    mock_response = Mock()
    mock_response.content = json.dumps({
        "sentiment_forecast": {
            "next_3_days": "看涨",
            "next_7_days": "中性",
            "turning_point_probability": 0.3
        },
        "market_psychology_cycle": {
            "current_phase": "乐观",
            "phase_confidence": 0.75
        },
        "investment_recommendation": {
            "sentiment_based_action": "买入",
            "key_monitoring_metrics": ["恐惧贪婪指数", "社交量"]
        },
        "confidence_assessment": {
            "analysis_confidence": 0.85
        },
        "executive_summary": "当前市场情绪偏向乐观，建议适度买入"
    }, ensure_ascii=False)
    
    mock_llm_adapter.invoke.return_value = mock_response
    
    # 创建启用AI的分析师
    ai_analyst = SentimentAnalyst(config)
    ai_analyst.llm_adapter = mock_llm_adapter
    ai_analyst.ai_enabled = True
    
    print(f"🚀 执行AI增强分析...")
    ai_result = ai_analyst.analyze(data)
    
    if "error" in ai_result:
        print(f"❌ AI分析失败: {ai_result['error']}")
        return False
    
    print("✅ AI增强分析完成")
    
    # 检查AI增强结果结构
    if "ai_analysis" not in ai_result:
        print("❌ 缺少AI分析结果")
        return False
    
    if "enhanced_insights" not in ai_result:
        print("❌ 缺少增强洞察")
        return False
    
    if "final_assessment" not in ai_result:
        print("❌ 缺少最终评估")
        return False
    
    # 显示AI增强结果
    ai_analysis = ai_result.get("ai_analysis", {})
    enhanced_insights = ai_result.get("enhanced_insights", {})
    final_assessment = ai_result.get("final_assessment", {})
    
    print(f"📈 AI分析结果:")
    print(f"- 3天情绪预测: {ai_analysis.get('sentiment_forecast', {}).get('next_3_days', 'N/A')}")
    print(f"- 7天情绪预测: {ai_analysis.get('sentiment_forecast', {}).get('next_7_days', 'N/A')}")
    print(f"- 市场心理阶段: {ai_analysis.get('market_psychology_cycle', {}).get('current_phase', 'N/A')}")
    print(f"- AI建议: {ai_analysis.get('investment_recommendation', {}).get('sentiment_based_action', 'N/A')}")
    
    print(f"🔄 增强洞察:")
    sentiment_consensus = enhanced_insights.get("sentiment_consensus", {})
    print(f"- 传统vs AI情绪: {sentiment_consensus.get('traditional', 'N/A')} vs {sentiment_consensus.get('ai_forecast', 'N/A')}")
    print(f"- 情绪一致性: {sentiment_consensus.get('agreement', False)}")
    
    confidence_assessment = enhanced_insights.get("confidence_assessment", {})
    print(f"- 综合置信度: {confidence_assessment.get('combined', 0):.2f}")
    print(f"- 可靠性: {confidence_assessment.get('reliability', 'N/A')}")
    
    print(f"🎯 最终评估:")
    print(f"- 整体建议: {final_assessment.get('overall_recommendation', 'N/A')}")
    print(f"- 置信度: {final_assessment.get('confidence', 0):.2f}")
    print(f"- 执行摘要: {final_assessment.get('executive_summary', 'N/A')}")
    
    # 测试AI关闭时的降级机制
    print(f"🛡️ 测试AI降级机制...")
    ai_analyst.ai_enabled = False
    fallback_result = ai_analyst.analyze(data)
    
    if "ai_analysis" in fallback_result:
        print("❌ AI关闭时仍返回AI分析结果")
        return False
    
    print("✅ AI降级机制正常")
    
    # 测试prompt构建
    print(f"📝 测试prompt构建...")
    prompt = ai_analyst._build_sentiment_analysis_prompt(traditional_result, data)
    
    if not prompt or len(prompt) < 1000:
        print("❌ Prompt构建失败或过短")
        return False
    
    print(f"✅ Prompt构建成功 (长度: {len(prompt)} 字符)")
    
    # 检查prompt关键部分
    required_sections = [
        "基本信息", "原始情绪数据", "量化分析结果", 
        "分析要求", "输出格式", "Twitter情绪数据", 
        "恐惧贪婪指数", "投资决策支持"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in prompt:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Prompt缺少关键部分: {', '.join(missing_sections)}")
        return False
    
    print("✅ Prompt包含所有关键部分")
    
    print("\n🎉 SentimentAnalyst AI集成测试全部通过!")
    print("\n📋 测试总结:")
    print("✅ 传统情绪分析功能正常")
    print("✅ AI适配器集成成功")
    print("✅ AI增强分析流程完整")
    print("✅ 结果融合逻辑正确")
    print("✅ AI降级机制可靠")
    print("✅ Prompt模板完善")
    
    return True

def test_prompt_template_quality():
    """测试prompt模板质量"""
    print("\n📝 测试Prompt模板质量...")
    
    config = {
        "llm_config": {"provider": "dashscope"},
        "ai_analysis_config": {"enabled": False}
    }
    
    analyst = SentimentAnalyst(config)
    
    # 创建测试数据
    traditional_analysis = {
        "overall_sentiment": {"sentiment": "bullish", "strength": "strong"},
        "sentiment_trend": {"trend": "improving", "momentum": "strong"},
        "twitter_analysis": {"sentiment": "bullish", "intensity": "high"},
        "reddit_analysis": {"sentiment": "bullish", "community_quality": "high"},
        "news_analysis": {"sentiment": "bullish", "institutional_interest": "high"},
        "fear_greed_analysis": {"market_psychology": "greed", "contrarian_signal": "strong"}
    }
    
    raw_data = {
        "symbol": "BTC/USDT",
        "base_currency": "BTC",
        "twitter_sentiment": {"tweet_count": 15420, "sentiment_score": 0.75},
        "reddit_sentiment": {"post_count": 850, "sentiment_score": 0.68},
        "fear_greed_index": {"fear_greed_value": 75, "classification": "Greed"}
    }
    
    prompt = analyst._build_sentiment_analysis_prompt(traditional_analysis, raw_data)
    
    # 检查prompt长度
    if len(prompt) < 5000:
        print(f"❌ Prompt过短: {len(prompt)} 字符")
        return False
    
    # 检查数据包含
    data_points = [
        "BTC/USDT", "15420", "0.75", "850", "0.68", "75", "Greed",
        "bullish", "strong", "improving"
    ]
    
    missing_data = []
    for point in data_points:
        if str(point) not in prompt:
            missing_data.append(point)
    
    if missing_data:
        print(f"❌ Prompt缺少关键数据: {missing_data}")
        return False
    
    # 检查分析要求结构
    analysis_requirements = [
        "情绪趋势预测", "市场情绪周期判断", "异常情绪信号识别",
        "交易心理洞察", "反向指标价值评估", "社交媒体影响力分析", 
        "投资决策支持"
    ]
    
    missing_requirements = []
    for req in analysis_requirements:
        if req not in prompt:
            missing_requirements.append(req)
    
    if missing_requirements:
        print(f"❌ Prompt缺少分析要求: {missing_requirements}")
        return False
    
    # 检查JSON输出格式
    json_fields = [
        "sentiment_forecast", "market_psychology_cycle", "anomaly_signals",
        "trading_psychology", "contrarian_analysis", "investment_recommendation",
        "confidence_assessment", "executive_summary"
    ]
    
    missing_fields = []
    for field in json_fields:
        if field not in prompt:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Prompt缺少JSON字段: {missing_fields}")
        return False
    
    print("✅ Prompt模板质量测试通过")
    print(f"- Prompt长度: {len(prompt):,} 字符")
    print(f"- 包含所有关键数据点")
    print(f"- 包含所有分析要求")
    print(f"- 包含完整JSON输出格式")
    
    return True

if __name__ == "__main__":
    print("🚀 启动SentimentAnalyst AI集成测试套件")
    print("=" * 60)
    
    success = True
    
    # 基础AI集成测试
    if not test_sentiment_analyst_ai_integration():
        success = False
    
    # Prompt模板质量测试
    if not test_prompt_template_quality():
        success = False
    
    print("=" * 60)
    if success:
        print("🎉 所有测试通过! SentimentAnalyst AI集成成功!")
    else:
        print("❌ 部分测试失败，需要修复")
        sys.exit(1)
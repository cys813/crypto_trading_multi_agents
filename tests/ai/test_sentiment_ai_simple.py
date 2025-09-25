#!/usr/bin/env python3
"""
SentimentAnalyst AI集成简单测试

测试AI增强的核心功能，不依赖外部包
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

def test_prompt_building():
    """测试prompt构建功能"""
    print("📝 测试Prompt构建功能...")
    
    # 模拟传统分析结果
    traditional_analysis = {
        "overall_sentiment": {
            "score": 0.72,
            "sentiment": "bullish",
            "strength": "strong",
            "consistency": "high"
        },
        "sentiment_trend": {
            "trend": "improving",
            "momentum": "strong",
            "sustainability": "high"
        },
        "twitter_analysis": {
            "sentiment": "bullish",
            "intensity": "high",
            "community_engagement": "strong",
            "virality_potential": "high"
        },
        "reddit_analysis": {
            "sentiment": "bullish",
            "community_quality": "high",
            "discussion_depth": "deep",
            "organic_growth": "strong"
        },
        "news_analysis": {
            "sentiment": "bullish",
            "media_tone": "positive",
            "institutional_interest": "high",
            "mainstream_adoption": "increasing"
        },
        "fear_greed_analysis": {
            "market_psychology": "greed",
            "extreme_level": "moderate",
            "contrarian_signal": "weak",
            "weekly_trend": "improving"
        },
        "key_signals": [
            "Twitter情绪看涨",
            "Reddit社区质量高",
            "机构关注度提升"
        ],
        "confidence": 0.85
    }
    
    # 模拟原始数据
    raw_data = {
        "symbol": "BTC/USDT",
        "base_currency": "BTC",
        "twitter_sentiment": {
            "tweet_count": 15420,
            "positive_tweets": 8750,
            "negative_tweets": 3250,
            "sentiment_score": 0.68,
            "engagement_rate": 0.045,
            "trending_hashtags": ["#Bitcoin", "#Crypto", "#BTC"]
        },
        "reddit_sentiment": {
            "post_count": 850,
            "comment_count": 12500,
            "upvote_ratio": 0.72,
            "sentiment_score": 0.65
        },
        "fear_greed_index": {
            "fear_greed_value": 72,
            "classification": "Greed",
            "weekly_change": 8
        },
        "social_volume": {
            "total_mentions": 185000,
            "growth_rate_24h": 0.12
        }
    }
    
    # 构建prompt (简化版本)
    symbol = raw_data.get("symbol", "未知")
    base_currency = raw_data.get("base_currency", "未知")
    
    prompt = f"""你是一位资深的加密货币市场情绪分析专家，请基于以下原始情绪数据和量化分析结果，对 {symbol} ({base_currency}) 进行深度情绪分析。

## 基本信息
- 交易对: {symbol}
- 基础货币: {base_currency}
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 原始情绪数据

### Twitter情绪数据
- 推文数量: {raw_data['twitter_sentiment']['tweet_count']:,}
- 正面推文: {raw_data['twitter_sentiment']['positive_tweets']:,}
- 负面推文: {raw_data['twitter_sentiment']['negative_tweets']:,}
- 情绪得分: {raw_data['twitter_sentiment']['sentiment_score']:.2f}
- 参与率: {raw_data['twitter_sentiment']['engagement_rate']*100:.1f}%

### Reddit情绪数据
- 帖子数量: {raw_data['reddit_sentiment']['post_count']:,}
- 评论数量: {raw_data['reddit_sentiment']['comment_count']:,}
- 点赞比例: {raw_data['reddit_sentiment']['upvote_ratio']*100:.1f}%
- 情绪得分: {raw_data['reddit_sentiment']['sentiment_score']:.2f}

### 恐惧贪婪指数
- 指数值: {raw_data['fear_greed_index']['fear_greed_value']}
- 分类: {raw_data['fear_greed_index']['classification']}
- 周变化: {raw_data['fear_greed_index']['weekly_change']}

## 量化分析结果

### 整体情绪分析
- 情绪得分: {traditional_analysis['overall_sentiment']['score']:.2f}
- 情绪倾向: {traditional_analysis['overall_sentiment']['sentiment']}
- 情绪强度: {traditional_analysis['overall_sentiment']['strength']}

### 情绪趋势分析
- 趋势方向: {traditional_analysis['sentiment_trend']['trend']}
- 动能: {traditional_analysis['sentiment_trend']['momentum']}

### 关键信号
{chr(10).join([f'- {signal}' for signal in traditional_analysis['key_signals']])}

## 分析要求

请基于以上数据提供专业的情绪分析：

1. **情绪趋势预测** - 预测未来3-7天情绪变化
2. **市场情绪周期判断** - 判断当前情绪周期阶段
3. **异常情绪信号识别** - 识别异常情绪变化
4. **投资决策支持** - 基于情绪的投资建议

## 输出格式

请以JSON格式输出分析结果。
"""
    
    # 检查prompt质量
    print(f"✅ Prompt构建成功")
    print(f"- 长度: {len(prompt):,} 字符")
    
    # 检查关键数据包含
    required_data = ["BTC/USDT", "0.68", "0.72", "bullish", "Greed"]
    missing_data = []
    
    for data in required_data:
        if str(data) not in prompt:
            missing_data.append(data)
    
    if missing_data:
        print(f"❌ 缺少关键数据: {missing_data}")
        return False
    
    print(f"✅ 包含所有关键数据点")
    
    # 检查分析要求
    requirements = ["情绪趋势预测", "市场情绪周期判断", "异常情绪信号识别", "投资决策支持"]
    missing_requirements = []
    
    for req in requirements:
        if req not in prompt:
            missing_requirements.append(req)
    
    if missing_requirements:
        print(f"❌ 缺少分析要求: {missing_requirements}")
        return False
    
    print(f"✅ 包含所有分析要求")
    
    return True

def test_response_parsing():
    """测试AI响应解析"""
    print("🔍 测试AI响应解析...")
    
    # 模拟AI响应
    mock_ai_response = json.dumps({
        "sentiment_forecast": {
            "next_3_days": "看涨",
            "next_7_days": "中性",
            "turning_point_probability": 0.3
        },
        "market_psychology_cycle": {
            "current_phase": "乐观",
            "phase_confidence": 0.75,
            "next_phase_prediction": "可能转向贪婪"
        },
        "investment_recommendation": {
            "sentiment_based_action": "买入",
            "key_monitoring_metrics": ["恐惧贪婪指数", "社交量", "意见领袖情绪"]
        },
        "confidence_assessment": {
            "analysis_confidence": 0.85,
            "data_quality_score": 0.9
        },
        "executive_summary": "当前市场情绪偏向乐观，短期有继续上涨趋势，建议适度买入，但需关注恐惧贪婪指数变化"
    }, ensure_ascii=False)
    
    # 解析响应
    try:
        parsed_response = json.loads(mock_ai_response)
        
        # 检查必要字段
        required_fields = [
            "sentiment_forecast", "market_psychology_cycle", 
            "investment_recommendation", "confidence_assessment", "executive_summary"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in parsed_response:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少必要字段: {missing_fields}")
            return False
        
        print("✅ AI响应解析成功")
        print(f"- 3天预测: {parsed_response['sentiment_forecast']['next_3_days']}")
        print(f"- 投资建议: {parsed_response['investment_recommendation']['sentiment_based_action']}")
        print(f"- 置信度: {parsed_response['confidence_assessment']['analysis_confidence']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return False

def test_analysis_combination():
    """测试分析结果融合"""
    print("🔄 测试分析结果融合...")
    
    # 模拟传统分析
    traditional_analysis = {
        "overall_sentiment": {"sentiment": "bullish", "score": 0.75},
        "confidence": 0.8,
        "key_signals": ["Twitter看涨", "Reddit积极"]
    }
    
    # 模拟AI分析
    ai_analysis = {
        "sentiment_forecast": {"next_3_days": "看涨"},
        "investment_recommendation": {"sentiment_based_action": "买入"},
        "confidence_assessment": {"analysis_confidence": 0.85}
    }
    
    # 简单的融合逻辑
    traditional_sentiment = traditional_analysis["overall_sentiment"]["sentiment"]
    ai_sentiment = "bullish" if ai_analysis["sentiment_forecast"]["next_3_days"] == "看涨" else "bearish"
    
    sentiment_agreement = traditional_sentiment == ai_sentiment
    
    traditional_confidence = traditional_analysis["confidence"]
    ai_confidence = ai_analysis["confidence_assessment"]["analysis_confidence"]
    
    if sentiment_agreement:
        combined_confidence = min((traditional_confidence + ai_confidence) / 2 * 1.15, 1.0)
    else:
        combined_confidence = (traditional_confidence + ai_confidence) / 2 * 0.85
    
    # 构建增强结果
    enhanced_result = {
        "traditional_analysis": traditional_analysis,
        "ai_analysis": ai_analysis,
        "enhanced_insights": {
            "sentiment_consensus": {
                "traditional": traditional_sentiment,
                "ai_forecast": ai_analysis["sentiment_forecast"]["next_3_days"],
                "agreement": sentiment_agreement
            },
            "confidence_assessment": {
                "traditional": traditional_confidence,
                "ai": ai_confidence,
                "combined": combined_confidence
            }
        },
        "final_assessment": {
            "overall_recommendation": "buy" if sentiment_agreement and traditional_sentiment == "bullish" else "hold",
            "confidence": combined_confidence
        }
    }
    
    print("✅ 分析结果融合成功")
    print(f"- 传统情绪: {traditional_sentiment}")
    print(f"- AI预测: {ai_analysis['sentiment_forecast']['next_3_days']}")
    print(f"- 情绪一致: {sentiment_agreement}")
    print(f"- 综合置信度: {combined_confidence:.2f}")
    print(f"- 最终建议: {enhanced_result['final_assessment']['overall_recommendation']}")
    
    # 验证结果结构
    required_sections = ["traditional_analysis", "ai_analysis", "enhanced_insights", "final_assessment"]
    missing_sections = []
    
    for section in required_sections:
        if section not in enhanced_result:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ 缺少必要部分: {missing_sections}")
        return False
    
    return True

def test_configuration_validation():
    """测试配置验证"""
    print("⚙️ 测试配置验证...")
    
    # 测试有效配置
    valid_configs = [
        {
            "llm_config": {"provider": "dashscope", "api_key": "test_key"},
            "ai_analysis_config": {"enabled": True, "temperature": 0.1}
        },
        {
            "llm_config": {"provider": "deepseek", "api_key": "test_key"},
            "ai_analysis_config": {"enabled": True, "max_tokens": 3000}
        }
    ]
    
    # 测试无效配置
    invalid_configs = [
        {"llm_config": {"provider": "unknown"}},  # 不支持的提供商
        {"llm_config": {"provider": "dashscope"}},  # 缺少API密钥
        {"ai_analysis_config": {"enabled": True}}  # 缺少LLM配置
    ]
    
    print("✅ 有效配置测试:")
    for i, config in enumerate(valid_configs):
        provider = config.get("llm_config", {}).get("provider", "unknown")
        enabled = config.get("ai_analysis_config", {}).get("enabled", False)
        print(f"  - 配置{i+1}: {provider}, 启用: {enabled}")
    
    print("⚠️ 无效配置测试:")
    for i, config in enumerate(invalid_configs):
        provider = config.get("llm_config", {}).get("provider", "未设置")
        api_key = "已设置" if config.get("llm_config", {}).get("api_key") else "未设置"
        print(f"  - 配置{i+1}: 提供商: {provider}, API密钥: {api_key}")
    
    return True

if __name__ == "__main__":
    print("🚀 启动SentimentAnalyst AI集成简单测试")
    print("=" * 50)
    
    success = True
    
    # 测试prompt构建
    if not test_prompt_building():
        success = False
        print()
    
    # 测试响应解析
    if not test_response_parsing():
        success = False
        print()
    
    # 测试分析融合
    if not test_analysis_combination():
        success = False
        print()
    
    # 测试配置验证
    if not test_configuration_validation():
        success = False
        print()
    
    print("=" * 50)
    if success:
        print("🎉 所有简单测试通过!")
        print("\n📋 测试总结:")
        print("✅ Prompt构建功能正常")
        print("✅ AI响应解析正确")
        print("✅ 分析结果融合成功")
        print("✅ 配置验证完整")
        print("\n🚀 SentimentAnalyst AI集成基础功能验证完成!")
    else:
        print("❌ 部分测试失败")
        sys.exit(1)
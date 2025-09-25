#!/usr/bin/env python3
"""
DOGE行情AI模型分析测试
展示详细的数据过程，包括给LLM的原始数据和LLM的原始输出结果
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def simulate_doge_market_data():
    """模拟DOGE市场数据"""
    print("📊 模拟DOGE市场数据收集...")
    
    # 模拟当前DOGE价格数据
    doge_data = {
        "symbol": "DOGE/USDT",
        "current_price": 0.3875,
        "price_change_24h": 0.0234,
        "price_change_percentage_24h": 6.43,
        "volume_24h": 2847293847.23,
        "market_cap": 57238947382.94,
        "market_cap_rank": 8,
        
        # 技术指标数据
        "technical_indicators": {
            "rsi_14": 68.34,
            "macd": {
                "macd": 0.0023,
                "signal": 0.0019,
                "histogram": 0.0004
            },
            "bollinger_bands": {
                "upper": 0.4124,
                "middle": 0.3876,
                "lower": 0.3628
            },
            "moving_averages": {
                "ma_20": 0.3654,
                "ma_50": 0.3421,
                "ma_200": 0.2987
            }
        },
        
        # 情绪数据
        "sentiment_data": {
            "twitter_sentiment": {
                "sentiment_score": 0.72,
                "tweet_volume_24h": 15734,
                "positive_tweets": 11286,
                "negative_tweets": 2234,
                "neutral_tweets": 2214,
                "engagement_rate": 0.043,
                "trending_keywords": ["doge", "moon", "hodl", "bullish", "elon"]
            },
            "reddit_sentiment": {
                "sentiment_score": 0.68,
                "posts_24h": 423,
                "upvote_ratio": 0.81,
                "comments_24h": 2847,
                "top_subreddits": ["dogecoin", "cryptocurrency", "wallstreetbets"]
            },
            "fear_greed_index": {
                "current_value": 74,
                "classification": "Greed",
                "last_update": "2025-08-07T15:30:00Z"
            }
        },
        
        # 链上数据
        "onchain_data": {
            "active_addresses_24h": 127394,
            "transaction_count_24h": 45823,
            "whale_transactions": {
                "large_transactions_24h": 23,
                "whale_accumulation": True,
                "net_flow_exchanges": -2847392.43
            },
            "network_activity": {
                "hash_rate_change": 3.2,
                "network_growth": 0.8
            }
        },
        
        # 新闻情绪
        "news_sentiment": {
            "sentiment_score": 0.65,
            "article_count_24h": 47,
            "positive_news": 31,
            "negative_news": 8,
            "neutral_news": 8,
            "key_topics": ["doge payments", "elon musk", "crypto adoption", "market rally"]
        },
        
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"   ✅ DOGE当前价格: ${doge_data['current_price']}")
    print(f"   ✅ 24h涨跌: +{doge_data['price_change_percentage_24h']:.2f}%")
    print(f"   ✅ Twitter情绪得分: {doge_data['sentiment_data']['twitter_sentiment']['sentiment_score']}")
    print(f"   ✅ 恐慌贪婪指数: {doge_data['sentiment_data']['fear_greed_index']['current_value']} ({doge_data['sentiment_data']['fear_greed_index']['classification']})")
    
    return doge_data

def prepare_traditional_analysis(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行传统规则分析"""
    print("\n🔍 执行传统规则分析...")
    
    # 技术分析
    technical_signals = []
    rsi = market_data["technical_indicators"]["rsi_14"]
    if rsi > 70:
        technical_signals.append("RSI超买信号")
    elif rsi > 50:
        technical_signals.append("RSI中性偏强")
    
    # 价格趋势分析
    price_trend = "上涨" if market_data["price_change_24h"] > 0 else "下跌"
    trend_strength = abs(market_data["price_change_percentage_24h"])
    
    # 情绪分析
    twitter_sentiment = market_data["sentiment_data"]["twitter_sentiment"]["sentiment_score"]
    reddit_sentiment = market_data["sentiment_data"]["reddit_sentiment"]["sentiment_score"]
    overall_sentiment = (twitter_sentiment + reddit_sentiment) / 2
    
    # 链上分析
    whale_activity = market_data["onchain_data"]["whale_transactions"]["whale_accumulation"]
    exchange_flow = market_data["onchain_data"]["whale_transactions"]["net_flow_exchanges"]
    
    traditional_analysis = {
        "technical_analysis": {
            "trend": price_trend,
            "trend_strength": trend_strength,
            "rsi_signal": "超买" if rsi > 70 else "中性偏强" if rsi > 50 else "中性",
            "moving_average_position": "价格高于MA20/50/200" if market_data["current_price"] > market_data["technical_indicators"]["moving_averages"]["ma_200"] else "价格低于长期均线",
            "bollinger_position": "接近上轨" if market_data["current_price"] > market_data["technical_indicators"]["bollinger_bands"]["middle"] else "接近下轨"
        },
        "sentiment_analysis": {
            "overall_sentiment": overall_sentiment,
            "sentiment_level": "积极" if overall_sentiment > 0.6 else "中性" if overall_sentiment > 0.4 else "消极",
            "social_volume": "高" if market_data["sentiment_data"]["twitter_sentiment"]["tweet_volume_24h"] > 10000 else "中等",
            "fear_greed_status": market_data["sentiment_data"]["fear_greed_index"]["classification"]
        },
        "onchain_analysis": {
            "whale_activity": "积极买入" if whale_activity else "中性",
            "exchange_flow": "资金流出交易所" if exchange_flow < 0 else "资金流入交易所",
            "network_activity": "增长" if market_data["onchain_data"]["network_activity"]["network_growth"] > 0 else "下降"
        },
        "risk_assessment": {
            "volatility_risk": "高" if trend_strength > 5 else "中等",
            "sentiment_risk": "FOMO风险" if overall_sentiment > 0.7 else "情绪恐慌" if overall_sentiment < 0.3 else "中性",
            "technical_risk": "超买风险" if rsi > 70 else "技术面健康"
        },
        "key_signals": technical_signals + [
            f"24小时涨幅{trend_strength:.1f}%",
            f"社交媒体情绪{overall_sentiment:.2f}",
            "巨鲸持续买入" if whale_activity else "巨鲸活动平静"
        ],
        "confidence_score": 0.75,
        "recommendation": "谨慎看多" if overall_sentiment > 0.6 and price_trend == "上涨" else "观望"
    }
    
    print(f"   ✅ 技术面: {traditional_analysis['technical_analysis']['trend']} (强度: {trend_strength:.1f}%)")
    print(f"   ✅ 情绪面: {traditional_analysis['sentiment_analysis']['sentiment_level']} ({overall_sentiment:.2f})")
    print(f"   ✅ 链上: {traditional_analysis['onchain_analysis']['whale_activity']}")
    print(f"   ✅ 风险评估: {traditional_analysis['risk_assessment']['technical_risk']}")
    print(f"   ✅ 建议: {traditional_analysis['recommendation']}")
    
    return traditional_analysis

def build_llm_analysis_prompt(market_data: Dict[str, Any], traditional_analysis: Dict[str, Any]) -> str:
    """构建给LLM的分析提示词"""
    print("\n📝 构建LLM分析提示词...")
    
    prompt = f"""
请作为专业的加密货币分析师，基于以下DOGE(狗狗币)的综合市场数据进行深度分析。

## 原始市场数据摘要:

### 基础行情数据:
- 当前价格: ${market_data['current_price']}
- 24小时变化: {market_data['price_change_percentage_24h']:+.2f}% (${market_data['price_change_24h']:+.4f})
- 交易量: ${market_data['volume_24h']:,.0f}
- 市值排名: #{market_data['market_cap_rank']}

### 技术指标:
- RSI(14): {market_data['technical_indicators']['rsi_14']:.1f}
- MACD: {market_data['technical_indicators']['macd']['macd']:.4f}
- 布林带位置: 当前价格相对中轨的位置
- 移动平均线: MA20({market_data['technical_indicators']['moving_averages']['ma_20']:.4f}) | MA50({market_data['technical_indicators']['moving_averages']['ma_50']:.4f}) | MA200({market_data['technical_indicators']['moving_averages']['ma_200']:.4f})

### 社交媒体情绪:
- Twitter情绪得分: {market_data['sentiment_data']['twitter_sentiment']['sentiment_score']:.2f}
- 24小时推文量: {market_data['sentiment_data']['twitter_sentiment']['tweet_volume_24h']:,}
- 热门关键词: {', '.join(market_data['sentiment_data']['twitter_sentiment']['trending_keywords'])}
- Reddit情绪得分: {market_data['sentiment_data']['reddit_sentiment']['sentiment_score']:.2f}
- Reddit讨论热度: {market_data['sentiment_data']['reddit_sentiment']['posts_24h']}帖子

### 市场情绪指标:
- 恐慌贪婪指数: {market_data['sentiment_data']['fear_greed_index']['current_value']}/100 ({market_data['sentiment_data']['fear_greed_index']['classification']})

### 链上数据:
- 24小时活跃地址: {market_data['onchain_data']['active_addresses_24h']:,}
- 24小时交易笔数: {market_data['onchain_data']['transaction_count_24h']:,}
- 巨鲸交易: {market_data['onchain_data']['whale_transactions']['large_transactions_24h']}笔大额交易
- 交易所净流量: {market_data['onchain_data']['whale_transactions']['net_flow_exchanges']:,.2f} DOGE

### 新闻情绪:
- 新闻情绪得分: {market_data['news_sentiment']['sentiment_score']:.2f}
- 24小时相关新闻: {market_data['news_sentiment']['article_count_24h']}篇
- 主要话题: {', '.join(market_data['news_sentiment']['key_topics'])}

## 传统分析结果:

### 技术面分析:
- 价格趋势: {traditional_analysis['technical_analysis']['trend']} (强度: {traditional_analysis['technical_analysis']['trend_strength']:.1f}%)
- RSI信号: {traditional_analysis['technical_analysis']['rsi_signal']}
- 均线位置: {traditional_analysis['technical_analysis']['moving_average_position']}
- 布林带位置: {traditional_analysis['technical_analysis']['bollinger_position']}

### 情绪面分析:
- 综合情绪: {traditional_analysis['sentiment_analysis']['overall_sentiment']:.2f} ({traditional_analysis['sentiment_analysis']['sentiment_level']})
- 社交热度: {traditional_analysis['sentiment_analysis']['social_volume']}
- 恐慌贪婪状态: {traditional_analysis['sentiment_analysis']['fear_greed_status']}

### 链上分析:
- 巨鲸活动: {traditional_analysis['onchain_analysis']['whale_activity']}
- 交易所资金流向: {traditional_analysis['onchain_analysis']['exchange_flow']}
- 网络活跃度: {traditional_analysis['onchain_analysis']['network_activity']}

### 风险评估:
- 波动性风险: {traditional_analysis['risk_assessment']['volatility_risk']}
- 情绪风险: {traditional_analysis['risk_assessment']['sentiment_risk']}
- 技术面风险: {traditional_analysis['risk_assessment']['technical_risk']}

### 关键信号:
{chr(10).join([f"- {signal}" for signal in traditional_analysis['key_signals']])}

### 传统分析建议:
{traditional_analysis['recommendation']} (置信度: {traditional_analysis['confidence_score']:.0%})

## 请进行AI增强分析:

请基于以上原始数据和传统分析结果，从以下角度进行深度AI分析:

1. **市场心理分析**: 基于当前的社交媒体情绪、恐慌贪婪指数和新闻热度，分析市场参与者的心理状态和可能的行为模式

2. **趋势延续性判断**: 结合技术面、资金流向和情绪面，判断当前趋势的可持续性和潜在转折点

3. **风险点识别**: 识别传统分析可能遗漏的潜在风险因素和黑天鹅事件可能性

4. **异常信号检测**: 发现数据中的异常模式或者与历史行为不符的信号

5. **多维度相关性**: 分析技术面、基本面、情绪面和链上数据之间的相关性和潜在矛盾

6. **时间窗口预测**: 基于当前数据模式，预测关键价格点位和时间节点

请以JSON格式返回分析结果，包含以下字段:
{{
  "market_psychology": "市场心理状态分析",
  "trend_sustainability": "趋势延续性评估",
  "risk_factors": ["风险因素1", "风险因素2"],
  "anomaly_signals": ["异常信号1", "异常信号2"],
  "correlation_analysis": "多维度相关性分析",
  "key_levels": {{
    "support": [支撑位1, 支撑位2],
    "resistance": [阻力位1, 阻力位2]
  }},
  "time_predictions": {{
    "next_24h": "24小时内预期",
    "next_week": "一周内预期"
  }},
  "ai_confidence": 0.85,
  "ai_recommendation": "AI增强建议",
  "reasoning": "详细推理过程"
}}
"""
    
    return prompt.strip()

def simulate_llm_response() -> str:
    """模拟LLM的原始返回结果"""
    print("\n🤖 模拟LLM分析响应...")
    
    llm_response = """
{
  "market_psychology": "当前DOGE市场呈现典型的'贪婪但理性'状态。恐慌贪婪指数74显示市场贪婪，但并未达到极端贪婪(>80)。社交媒体情绪积极(0.72)，关键词'moon'、'hodl'、'bullish'表明散户仍保持乐观，但'elon'关键词的出现提示市场仍依赖外部催化剂。Reddit情绪相对冷静(0.68)，表明机构和有经验投资者更为谨慎。这种情绪分化可能预示着短期调整的可能。",
  
  "trend_sustainability": "当前上涨趋势的可持续性存在分歧信号。正面因素：(1)巨鲸持续买入，交易所净流出284万DOGE显示长期持有意愿；(2)网络活跃度增长0.8%，基本面支撑；(3)价格突破MA20/50，技术面向好。负面因素：(1)RSI达68.34，接近超买区域；(2)6.43%的单日涨幅可能触发获利回吐；(3)社交热度虽高但可能已过热。综合评估，短期内趋势可能放缓，但中期仍有向上空间。",
  
  "risk_factors": [
    "RSI超买风险：68.34接近70超买线，短期调整压力增加",
    "情绪过热风险：Twitter讨论量15,734条显示散户FOMO情绪浓厚",
    "外部依赖风险：热门关键词中'elon'的出现表明仍依赖马斯克等外部因素",
    "获利回吐风险：6.43%单日涨幅可能引发短期获利了结",
    "关联性风险：作为Meme币，DOGE与整体Meme板块关联度高，存在连带下跌风险"
  ],
  
  "anomaly_signals": [
    "巨鲸买入与散户热情的反差：大额交易23笔显示机构买入，但散户情绪过热，这种分化历史上常预示调整",
    "新闻情绪与价格涨幅不匹配：新闻情绪0.65相对温和，但价格涨幅6.43%较激进，可能存在投机成分",
    "链上活跃度与价格表现不同步：活跃地址127,394相对平稳，但价格波动剧烈，暗示交易集中度高"
  ],
  
  "correlation_analysis": "技术面与情绪面高度正相关，RSI上升与社交情绪改善同步，符合正常市场行为。但链上数据与价格表现存在轻微背离：网络基础指标增长温和(0.8%)，而价格表现激进(6.43%)，这种背离在短期可能导致价格回调以匹配基本面。巨鲸行为与散户情绪呈现分化，机构理性买入vs散户情绪化追涨，这种分化通常是市场阶段性顶部的前兆信号。",
  
  "key_levels": {
    "support": [0.3654, 0.3421],
    "resistance": [0.4124, 0.4350]
  },
  
  "time_predictions": {
    "next_24h": "预期在0.38-0.41区间震荡，突破0.41需要额外催化剂，跌破0.37则可能回调至MA20支撑",
    "next_week": "一周内看涨格局不变，目标价位0.42-0.45，但需关注RSI是否形成顶背离和情绪面降温"
  },
  
  "ai_confidence": 0.82,
  "ai_recommendation": "谨慎看多，建议分批建仓。当前位置适合轻仓试探，等待回调至0.365-0.37区间加仓。止损设置在0.34下方，目标价位0.42-0.45。重点关注RSI是否进入超买区域和社交情绪是否过热，一旦出现情绪降温信号应及时止盈。",
  
  "reasoning": "综合分析认为DOGE当前处于健康上升趋势中，但已进入相对高位区域。技术面偏强但接近超买，情绪面积极但存在过热风险，基本面支撑较好但改善幅度有限。AI模型识别出巨鲸买入与散户FOMO的分化信号，这通常预示着短期可能的调整。建议采取'涨不追，跌买入'的策略，在支撑位附近分批建仓，严格控制仓位和风险。"
}
"""
    
    return llm_response.strip()

def parse_and_combine_analysis(llm_response: str, traditional_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """解析LLM响应并与传统分析结合"""
    print("\n🔄 解析LLM响应并合并分析结果...")
    
    try:
        ai_analysis = json.loads(llm_response)
        print("   ✅ LLM响应解析成功")
    except json.JSONDecodeError as e:
        print(f"   ❌ LLM响应解析失败: {e}")
        ai_analysis = {"error": "LLM响应解析失败"}
    
    # 合并传统分析和AI分析
    final_analysis = {
        "symbol": "DOGE/USDT",
        "analysis_timestamp": datetime.now().isoformat(),
        "analysis_type": "hybrid_ai_enhanced",
        
        # 传统分析结果
        "traditional_analysis": traditional_analysis,
        
        # AI增强分析结果
        "ai_analysis": ai_analysis,
        
        # 综合评估
        "final_assessment": {
            "overall_sentiment": "谨慎乐观",
            "confidence_score": (traditional_analysis["confidence_score"] + ai_analysis.get("ai_confidence", 0.5)) / 2,
            "risk_level": "中等",
            "investment_advice": ai_analysis.get("ai_recommendation", traditional_analysis["recommendation"]),
            "key_price_levels": ai_analysis.get("key_levels", {}),
            "time_horizon_outlook": ai_analysis.get("time_predictions", {})
        },
        
        # 分析质量评估
        "analysis_quality": {
            "data_completeness": 0.95,
            "ai_enhancement": True if "ai_confidence" in ai_analysis else False,
            "signal_consistency": 0.87,
            "prediction_reliability": 0.82
        }
    }
    
    print(f"   ✅ 综合置信度: {final_analysis['final_assessment']['confidence_score']:.0%}")
    print(f"   ✅ 最终建议: {final_analysis['final_assessment']['investment_advice'][:50]}...")
    
    return final_analysis

def display_detailed_process(market_data: Dict[str, Any], traditional_analysis: Dict[str, Any], 
                           llm_prompt: str, llm_response: str, final_analysis: Dict[str, Any]):
    """展示详细的数据处理过程"""
    print("\n" + "="*80)
    print("📋 DOGE AI分析详细数据过程展示")
    print("="*80)
    
    # 1. 原始数据
    print("\n🔍 1. 收集的原始市场数据:")
    print("-" * 40)
    print(json.dumps(market_data, indent=2, ensure_ascii=False))
    
    # 2. 传统分析结果
    print("\n🧮 2. 传统规则分析结果:")
    print("-" * 40)
    print(json.dumps(traditional_analysis, indent=2, ensure_ascii=False))
    
    # 3. 发送给LLM的完整提示词
    print("\n📤 3. 发送给LLM的完整提示词:")
    print("-" * 40)
    print("提示词长度:", len(llm_prompt), "字符")
    print("\n提示词内容:")
    print(llm_prompt)
    
    # 4. LLM原始响应
    print("\n🤖 4. LLM的原始响应结果:")
    print("-" * 40)
    print("响应长度:", len(llm_response), "字符")
    print("\nLLM原始输出:")
    print(llm_response)
    
    # 5. 最终合并分析
    print("\n🎯 5. 最终合并分析结果:")
    print("-" * 40)
    print(json.dumps(final_analysis, indent=2, ensure_ascii=False, default=str))

def main():
    """主函数 - 执行完整的DOGE AI分析流程"""
    print("🚀 开始DOGE AI模型分析测试")
    print("="*60)
    
    # 更新任务状态
    print("📋 更新任务进度...")
    
    # 1. 模拟数据收集
    market_data = simulate_doge_market_data()
    print("   ✅ 任务1完成: DOGE行情数据收集")
    
    # 2. 执行传统分析
    traditional_analysis = prepare_traditional_analysis(market_data)
    print("   ✅ 任务2完成: 传统规则分析")
    
    # 3. 构建LLM提示词
    llm_prompt = build_llm_analysis_prompt(market_data, traditional_analysis)
    print("   ✅ 任务3完成: LLM分析数据准备")
    print(f"   📝 提示词长度: {len(llm_prompt)} 字符")
    
    # 4. 模拟LLM分析（实际环境中会调用真实的LLM服务）
    llm_response = simulate_llm_response()
    print("   ✅ 任务4完成: AI模型分析执行")
    print(f"   🤖 LLM响应长度: {len(llm_response)} 字符")
    
    # 5. 合并分析结果
    final_analysis = parse_and_combine_analysis(llm_response, traditional_analysis)
    print("   ✅ 任务5完成: 分析结果合并")
    
    # 6. 展示详细过程
    display_detailed_process(market_data, traditional_analysis, llm_prompt, llm_response, final_analysis)
    print("\n   ✅ 任务6完成: 详细数据过程展示")
    
    # 生成总结报告
    print("\n" + "="*80)
    print("📊 DOGE AI分析总结")
    print("="*80)
    
    final_assessment = final_analysis["final_assessment"]
    print(f"🎯 投资建议: {final_assessment['investment_advice']}")
    print(f"📈 整体情绪: {final_assessment['overall_sentiment']}")
    print(f"🔢 综合置信度: {final_assessment['confidence_score']:.0%}")
    print(f"⚠️  风险等级: {final_assessment['risk_level']}")
    
    if "key_price_levels" in final_assessment:
        levels = final_assessment["key_price_levels"]
        if "support" in levels:
            print(f"📉 支撑位: {levels['support']}")
        if "resistance" in levels:
            print(f"📈 阻力位: {levels['resistance']}")
    
    print(f"\n✅ AI分析完成! 数据质量评分: {final_analysis['analysis_quality']['data_completeness']:.0%}")
    
    return final_analysis

if __name__ == "__main__":
    try:
        result = main()
        print("\n🎉 DOGE AI分析测试成功完成!")
    except Exception as e:
        print(f"\n❌ DOGE AI分析测试失败: {e}")
        import traceback
        traceback.print_exc()
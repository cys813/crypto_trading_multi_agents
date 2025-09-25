#!/usr/bin/env python3
"""
测试OnchainAnalyst的AI增强分析功能
"""

import sys
import os
from pathlib import Path
import json
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crypto_trading_agents.agents.analysts.onchain_analyst import OnchainAnalyst
from src.crypto_trading_agents.config.ai_analysis_config import get_ai_analysis_config

def create_test_config() -> Dict[str, Any]:
    """创建测试配置"""
    config = {
        # 基础配置
        "crypto_config": {
            "supported_chains": ["ethereum", "bitcoin", "solana", "polygon", "binance-smart-chain"]
        },
        
        # AI配置 - 使用演示模式避免需要真实API key
        "ai_analysis_config": {
            "enabled": True,
            "temperature": 0.1,
            "max_tokens": 3000,
        },
        
        "llm_config": {
            "provider": "demo",  # 使用演示模式
            "model": "demo-model",
            "api_key": "demo-key",
        }
    }
    
    return config

def create_mock_onchain_data() -> Dict[str, Any]:
    """创建模拟链上数据"""
    return {
        "symbol": "BTC/USDT",
        "base_currency": "BTC", 
        "chain": "bitcoin",
        "end_date": "2024-01-15",
        
        # 活跃地址数据
        "active_addresses": {
            "daily_active": 920000,
            "weekly_active": 3800000,
            "monthly_active": 9200000,
            "growth_rate_7d": 0.08,
            "growth_rate_30d": 0.15,
            "historical_avg": 820000,
            "percentile": 82,
        },
        
        # 交易指标数据
        "transaction_metrics": {
            "daily_transactions": 1380000,
            "average_fee": 18.5,
            "total_fees": 25530000,
            "large_transactions": 1580,
            "transaction_growth": 0.12,
            "fee_trend": "increasing",
        },
        
        # 交易所流量数据
        "exchange_flows": {
            "exchange_inflows": 18500,
            "exchange_outflows": 15200,
            "net_flow": -3300,  # 净流出
            "inflow_trend": "decreasing",
            "outflow_trend": "increasing", 
            "exchange_balance": 2800000,
            "balance_change_24h": -0.15,
        },
        
        # 巨鲸活动数据
        "whale_activity": {
            "whale_transactions": 52,
            "whale_inflows": 9200,
            "whale_outflows": 7100,
            "net_whale_flow": -2100,
            "whale_concentration": 0.58,
            "large_holder_count": 9200,
            "accumulation_pattern": True,
        },
        
        # 网络健康数据 (BTC)
        "network_health": {
            "hash_rate": 520000000000000,  # 520 EH/s
            "difficulty": 78000000000000,
            "mining_revenue": 42000000,
            "network_nodes": 16500,
            "network_uptime": 0.9998,
        },
        
        # DeFi指标数据
        "defi_metrics": {
            "tvl": 28000000000,  # 280亿美元
            "defi_users": 5200000,
            "protocol_count": 420,
            "lending_volume": 950000000,
            "dex_volume": 1350000000,
            "yield_farming_tvl": 9200000000,
        },
        
        # 持币分布数据
        "holder_distribution": {
            "top_10_holders": 0.12,
            "top_100_holders": 0.32,
            "retail_holders": 0.68,
            "holder_growth": 0.09,
            "average_balance": 0.92,
            "gini_coefficient": 0.68,
        }
    }

class MockLLMAdapter:
    """模拟LLM适配器用于测试"""
    
    def invoke(self, messages):
        """模拟LLM调用"""
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        # 返回模拟的JSON格式AI分析结果
        mock_analysis = {
            "network_health_analysis": {
                "current_status": "健康",
                "growth_sustainability": "可持续",
                "network_maturity": "成熟期",
                "development_trend": "上升"
            },
            "capital_flow_analysis": {
                "exchange_flow_signal": "积累",
                "whale_behavior_impact": "看涨",
                "institutional_activity": "增加",
                "retail_participation": "活跃"
            },
            "defi_ecosystem_assessment": {
                "tvl_trend": "增长",
                "innovation_level": "高",
                "adoption_rate": "快速",
                "risk_level": "中"
            },
            "onchain_sentiment": {
                "overall_sentiment": "看涨",
                "sentiment_strength": 0.75,
                "divergence_signals": ["交易所净流出", "巨鲸积累"],
                "turning_point_probability": 0.25
            },
            "investment_recommendation": {
                "timeframe": "中期",
                "recommendation": "看涨",
                "key_monitoring_metrics": ["交易所余额变化", "巨鲸流量", "网络活跃度"],
                "entry_signals": ["持续净流出", "网络活跃度增长"],
                "exit_signals": ["大量流入交易所", "网络活跃度下降"]
            },
            "market_cycle_analysis": {
                "current_phase": "牛市中期",
                "cycle_confidence": 0.8,
                "transition_indicators": ["链上活跃度", "机构采用率"],
                "historical_comparison": "相似"
            },
            "risk_opportunities": {
                "primary_risks": ["监管不确定性", "技术风险"],
                "key_opportunities": ["机构采用增加", "DeFi生态发展"],
                "risk_mitigation": ["分散投资", "定期监控链上指标"]
            },
            "confidence_assessment": {
                "analysis_confidence": 0.82,
                "data_quality_score": 0.95,
                "prediction_reliability": "高"
            },
            "executive_summary": "基于链上数据分析，BTC当前处于健康的上升趋势中。交易所净流出、巨鲸积累行为以及网络活跃度的持续增长都表明市场处于积累阶段。建议中期看涨，但需密切监控交易所流量变化和网络指标。"
        }
        
        return MockResponse(json.dumps(mock_analysis, ensure_ascii=False, indent=2))

def test_traditional_analysis():
    """测试传统链上分析功能"""
    print("=== 测试传统链上分析功能 ===")
    
    # 创建配置，禁用AI分析
    config = create_test_config()
    config["ai_analysis_config"]["enabled"] = False
    
    # 创建分析师
    analyst = OnchainAnalyst(config)
    
    # 创建测试数据
    test_data = create_mock_onchain_data()
    
    # 执行分析
    result = analyst.analyze(test_data)
    
    print("传统分析结果:")
    print(f"- 链上健康度: {result.get('onchain_health', {}).get('status', 'unknown')}")
    print(f"- 市场情绪: {result.get('market_sentiment', {}).get('sentiment', 'unknown')}")
    print(f"- 风险等级: {result.get('risk_metrics', {}).get('risk_level', 'unknown')}")
    print(f"- 置信度: {result.get('confidence', 0):.2f}")
    print(f"- 关键洞察: {len(result.get('key_insights', []))}条")
    print()
    
    return result

def test_ai_enhanced_analysis():
    """测试AI增强链上分析功能"""
    print("=== 测试AI增强链上分析功能 ===")
    
    # 创建启用AI的配置
    config = create_test_config()
    
    # 创建分析师
    analyst = OnchainAnalyst(config)
    
    # 手动设置模拟LLM适配器
    analyst.llm_adapter = MockLLMAdapter()
    
    # 创建测试数据
    test_data = create_mock_onchain_data()
    
    # 执行AI增强分析
    result = analyst.analyze(test_data)
    
    print("AI增强分析结果:")
    
    # 传统分析部分
    traditional = result.get("traditional_analysis", {})
    print(f"- 传统分析置信度: {traditional.get('confidence', 0):.2f}")
    
    # AI分析部分
    ai_analysis = result.get("ai_analysis", {})
    print(f"- AI分析置信度: {ai_analysis.get('confidence_assessment', {}).get('analysis_confidence', 0):.2f}")
    print(f"- AI情绪判断: {ai_analysis.get('onchain_sentiment', {}).get('overall_sentiment', 'unknown')}")
    print(f"- AI投资建议: {ai_analysis.get('investment_recommendation', {}).get('recommendation', 'unknown')}")
    
    # 增强洞察
    enhanced = result.get("enhanced_insights", {})
    sentiment_consensus = enhanced.get("sentiment_consensus", {})
    print(f"- 情绪一致性: {sentiment_consensus.get('agreement', False)}")
    print(f"- 综合置信度: {enhanced.get('confidence_assessment', {}).get('combined', 0):.2f}")
    
    # 最终评估
    final = result.get("final_assessment", {})
    print(f"- 最终建议: {final.get('overall_recommendation', 'unknown')}")
    print(f"- 监控指标: {len(final.get('monitoring_metrics', []))}个")
    print(f"- 执行总结: {final.get('executive_summary', 'N/A')[:100]}...")
    print()
    
    return result

def test_data_collection():
    """测试数据收集功能"""
    print("=== 测试数据收集功能 ===")
    
    config = create_test_config()
    analyst = OnchainAnalyst(config)
    
    # 测试数据收集
    collected_data = analyst.collect_data("BTC/USDT", "2024-01-15")
    
    print("数据收集结果:")
    print(f"- 交易对: {collected_data.get('symbol', 'unknown')}")
    print(f"- 基础货币: {collected_data.get('base_currency', 'unknown')}")
    print(f"- 区块链: {collected_data.get('chain', 'unknown')}")
    print(f"- 数据字段数: {len(collected_data.keys())}")
    print()
    
    return collected_data

def display_analysis_comparison(traditional_result, ai_enhanced_result):
    """显示分析结果对比"""
    print("=== 传统分析 vs AI增强分析对比 ===")
    
    # 置信度对比
    traditional_conf = traditional_result.get("confidence", 0)
    ai_enhanced_conf = ai_enhanced_result.get("enhanced_insights", {}).get("confidence_assessment", {}).get("combined", 0)
    
    print(f"置信度对比:")
    print(f"- 传统分析: {traditional_conf:.2f}")
    print(f"- AI增强: {ai_enhanced_conf:.2f}")
    print(f"- 提升: {(ai_enhanced_conf - traditional_conf)*100:+.1f}%")
    print()
    
    # 情绪分析对比
    traditional_sentiment = traditional_result.get("market_sentiment", {}).get("sentiment", "unknown")
    ai_sentiment = ai_enhanced_result.get("ai_analysis", {}).get("onchain_sentiment", {}).get("overall_sentiment", "unknown")
    
    print(f"情绪分析对比:")
    print(f"- 传统分析: {traditional_sentiment}")
    print(f"- AI分析: {ai_sentiment}")
    print(f"- 一致性: {ai_enhanced_result.get('enhanced_insights', {}).get('sentiment_consensus', {}).get('agreement', False)}")
    print()
    
    # 洞察丰富度对比
    traditional_insights = len(traditional_result.get("key_insights", []))
    ai_monitoring_metrics = len(ai_enhanced_result.get("final_assessment", {}).get("monitoring_metrics", []))
    
    print(f"洞察丰富度:")
    print(f"- 传统关键洞察: {traditional_insights}条")
    print(f"- AI监控指标: {ai_monitoring_metrics}个")
    print()

def main():
    """主测试函数"""
    print("🔗 OnchainAnalyst AI增强分析测试")
    print("=" * 50)
    
    try:
        # 1. 测试数据收集
        collected_data = test_data_collection()
        
        # 2. 测试传统分析
        traditional_result = test_traditional_analysis()
        
        # 3. 测试AI增强分析
        ai_enhanced_result = test_ai_enhanced_analysis()
        
        # 4. 对比分析结果
        display_analysis_comparison(traditional_result, ai_enhanced_result)
        
        # 5. 保存测试结果
        test_results = {
            "timestamp": "2024-01-15T10:30:00",
            "collected_data": collected_data,
            "traditional_analysis": traditional_result,
            "ai_enhanced_analysis": ai_enhanced_result
        }
        
        with open("onchain_ai_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print("✅ 所有测试完成！结果已保存到 onchain_ai_test_results.json")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
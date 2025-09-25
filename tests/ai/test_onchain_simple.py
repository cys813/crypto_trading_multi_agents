#!/usr/bin/env python3
"""
简化的OnchainAnalyst AI增强分析测试
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any

# 直接导入OnchainAnalyst模块
sys.path.insert(0, str(Path(__file__).parent / "crypto_trading_agents"))

# 模拟LLM适配器
class MockLLMAdapter:
    """模拟LLM适配器"""
    
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
            "confidence_assessment": {
                "analysis_confidence": 0.82,
                "data_quality_score": 0.95,
                "prediction_reliability": "高"
            },
            "executive_summary": "基于链上数据分析，BTC当前处于健康的上升趋势中。交易所净流出、巨鲸积累行为以及网络活跃度的持续增长都表明市场处于积累阶段。"
        }
        
        return MockResponse(json.dumps(mock_analysis, ensure_ascii=False, indent=2))

def test_onchain_analyst_direct():
    """直接测试OnchainAnalyst类"""
    print("🔗 直接测试OnchainAnalyst AI增强功能")
    print("=" * 50)
    
    # 导入OnchainAnalyst类
    try:
        from agents.analysts.onchain_analyst import OnchainAnalyst
    except ImportError as e:
        print(f"导入失败: {e}")
        return
    
    # 创建测试配置
    config = {
        "crypto_config": {
            "supported_chains": ["ethereum", "bitcoin", "solana"]
        },
        "ai_analysis_config": {
            "enabled": True,
            "temperature": 0.1,
            "max_tokens": 3000,
        },
        "llm_config": {
            "provider": "demo",
            "model": "demo-model",
            "api_key": "demo-key",
        }
    }
    
    # 创建模拟数据
    test_data = {
        "symbol": "BTC/USDT",
        "base_currency": "BTC", 
        "chain": "bitcoin",
        "end_date": "2024-01-15",
        
        "active_addresses": {
            "daily_active": 920000,
            "weekly_active": 3800000,
            "growth_rate_7d": 0.08,
            "growth_rate_30d": 0.15,
            "historical_avg": 820000,
            "percentile": 82,
        },
        
        "transaction_metrics": {
            "daily_transactions": 1380000,
            "average_fee": 18.5,
            "total_fees": 25530000,
            "large_transactions": 1580,
            "transaction_growth": 0.12,
            "fee_trend": "increasing",
        },
        
        "exchange_flows": {
            "exchange_inflows": 18500,
            "exchange_outflows": 15200,
            "net_flow": -3300,  # 净流出
            "exchange_balance": 2800000,
            "balance_change_24h": -0.15,
        },
        
        "whale_activity": {
            "whale_transactions": 52,
            "whale_inflows": 9200,
            "whale_outflows": 7100,
            "net_whale_flow": -2100,
            "whale_concentration": 0.58,
            "accumulation_pattern": True,
        },
        
        "network_health": {
            "hash_rate": 520000000000000,
            "difficulty": 78000000000000,
            "mining_revenue": 42000000,
            "network_nodes": 16500,
            "network_uptime": 0.9998,
        },
    }
    
    try:
        # 1. 测试传统分析
        print("1. 测试传统分析（AI禁用）")
        config_no_ai = config.copy()
        config_no_ai["ai_analysis_config"]["enabled"] = False
        
        analyst_traditional = OnchainAnalyst(config_no_ai)
        traditional_result = analyst_traditional.analyze(test_data)
        
        print(f"   - 健康状态: {traditional_result.get('onchain_health', {}).get('status', 'unknown')}")
        print(f"   - 市场情绪: {traditional_result.get('market_sentiment', {}).get('sentiment', 'unknown')}")
        print(f"   - 风险等级: {traditional_result.get('risk_metrics', {}).get('risk_level', 'unknown')}")
        print(f"   - 置信度: {traditional_result.get('confidence', 0):.2f}")
        print()
        
        # 2. 测试AI增强分析
        print("2. 测试AI增强分析")
        analyst_ai = OnchainAnalyst(config)
        
        # 设置模拟LLM适配器
        analyst_ai.llm_adapter = MockLLMAdapter()
        
        ai_result = analyst_ai.analyze(test_data)
        
        print(f"   - 传统置信度: {ai_result.get('traditional_analysis', {}).get('confidence', 0):.2f}")
        print(f"   - AI置信度: {ai_result.get('ai_analysis', {}).get('confidence_assessment', {}).get('analysis_confidence', 0):.2f}")
        print(f"   - 综合置信度: {ai_result.get('enhanced_insights', {}).get('confidence_assessment', {}).get('combined', 0):.2f}")
        print(f"   - AI情绪: {ai_result.get('ai_analysis', {}).get('onchain_sentiment', {}).get('overall_sentiment', 'unknown')}")
        print(f"   - 最终建议: {ai_result.get('final_assessment', {}).get('overall_recommendation', 'unknown')}")
        print()
        
        # 3. 展示AI分析的详细内容
        print("3. AI分析详细内容")
        ai_analysis = ai_result.get("ai_analysis", {})
        
        network_health = ai_analysis.get("network_health_analysis", {})
        print(f"   - 网络健康: {network_health.get('current_status', 'unknown')} ({network_health.get('development_trend', 'unknown')})")
        
        capital_flow = ai_analysis.get("capital_flow_analysis", {})
        print(f"   - 资金流向: {capital_flow.get('exchange_flow_signal', 'unknown')} ({capital_flow.get('whale_behavior_impact', 'unknown')})")
        
        final_assessment = ai_result.get("final_assessment", {})
        monitoring_metrics = final_assessment.get("monitoring_metrics", [])
        print(f"   - 监控指标: {', '.join(monitoring_metrics[:3])}...")
        print(f"   - 执行总结: {final_assessment.get('executive_summary', 'N/A')[:100]}...")
        print()
        
        # 4. 保存结果
        test_results = {
            "traditional_analysis": traditional_result,
            "ai_enhanced_analysis": ai_result,
            "test_timestamp": "2024-01-15T10:30:00"
        }
        
        with open("crypto_trading_agents/onchain_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print("✅ 测试完成！结果已保存到 onchain_test_results.json")
        
        # 5. 显示关键改进
        traditional_conf = traditional_result.get("confidence", 0)
        ai_enhanced_conf = ai_result.get("enhanced_insights", {}).get("confidence_assessment", {}).get("combined", 0)
        improvement = (ai_enhanced_conf - traditional_conf) * 100
        
        print(f"\n📊 AI增强效果:")
        print(f"   - 置信度提升: {improvement:+.1f}%")
        print(f"   - 分析维度: 从基础链上指标扩展到网络健康、资金流向、市场周期等多维度分析")
        print(f"   - 决策支持: 提供具体的监控指标和投资建议")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_onchain_analyst_direct()
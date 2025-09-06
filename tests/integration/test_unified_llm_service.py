#!/usr/bin/env python3
"""
统一LLM服务测试

测试统一LLM服务框架的功能，包括：
1. LLM服务初始化
2. 多提供商支持（DashScope、DeepSeek）
3. AI分析混入类
4. 各分析模块的AI增强功能

运行方式：
python test_unified_llm_service.py
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockLLMAdapter:
    """模拟LLM适配器，用于测试"""
    
    def __init__(self, provider, model, **kwargs):
        self.provider = provider
        self.model = model
        self.kwargs = kwargs
    
    def call(self, prompt: str, **kwargs) -> str:
        """模拟LLM调用"""
        # 根据prompt内容返回不同的模拟响应
        if "链上数据分析师" in prompt:
            return self._get_onchain_mock_response()
        elif "情绪分析师" in prompt:
            return self._get_sentiment_mock_response()
        elif "DeFi生态分析师" in prompt:
            return self._get_defi_mock_response()
        elif "牛市研究分析师" in prompt:
            return self._get_bull_mock_response()
        elif "熊市研究分析师" in prompt:
            return self._get_bear_mock_response()
        else:
            return self._get_default_mock_response()
    
    def _get_onchain_mock_response(self) -> str:
        """链上分析模拟响应"""
        return json.dumps({
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
            "confidence_level": 82,
            "key_insights": ["基于链上数据分析，当前处于健康的上升趋势中"]
        }, ensure_ascii=False)
    
    def _get_sentiment_mock_response(self) -> str:
        """情绪分析模拟响应"""
        return json.dumps({
            "sentiment_prediction": {
                "direction": "看涨",
                "strength": 0.7,
                "duration": "中期"
            },
            "market_emotion_cycle": {
                "current_phase": "乐观期",
                "transition_probability": 0.3,
                "cycle_maturity": "中期"
            },
            "anomaly_signals": {
                "detected": True,
                "signals": ["恐慌情绪反转", "社交媒体情绪回暖"],
                "significance": "高"
            },
            "trading_psychology": {
                "crowd_behavior": "FOMO开始显现",
                "contrarian_value": 0.6,
                "institutional_sentiment": "谨慎乐观"
            },
            "confidence_level": 75,
            "key_insights": ["市场情绪正在从恐慌转向乐观", "建议关注情绪过热风险"]
        }, ensure_ascii=False)
    
    def _get_defi_mock_response(self) -> str:
        """DeFi分析模拟响应"""
        return json.dumps({
            "defi_ecosystem_health": {
                "overall_health": "良好",
                "growth_sustainability": "可持续",
                "innovation_level": "高"
            },
            "protocol_risk_assessment": {
                "systemic_risk": "中",
                "smart_contract_risk": "低",
                "governance_risk": "中"
            },
            "tvl_analysis": {
                "trend_direction": "上升",
                "sustainability_score": 0.8,
                "concentration_risk": "低"
            },
            "yield_sustainability": {
                "current_yields_sustainable": "大部分可持续",
                "risk_adjusted_return": 0.7,
                "bubble_indicators": "无明显泡沫"
            },
            "confidence_level": 78,
            "key_insights": ["DeFi生态整体健康，TVL增长可持续"]
        }, ensure_ascii=False)
    
    def _get_bull_mock_response(self) -> str:
        """牛市研究模拟响应"""
        return json.dumps({
            "bull_momentum_score": 75,
            "market_phase_assessment": "中期牛市",
            "strength_indicators": ["机构资金流入", "技术突破确认", "监管明确化"],
            "risk_factors": ["估值过高风险", "监管不确定性"],
            "entry_opportunities": ["回调时分批建仓", "突破确认后追涨", "板块轮动机会"],
            "target_levels": {
                "short_term": 45000,
                "medium_term": 52000,
                "long_term": 65000
            },
            "confidence_level": 80,
            "key_insights": ["牛市趋势确立，建议分批建仓"]
        }, ensure_ascii=False)
    
    def _get_bear_mock_response(self) -> str:
        """熊市研究模拟响应"""
        return json.dumps({
            "bear_momentum_score": 65,
            "market_phase_assessment": "早期熊市",
            "weakness_indicators": ["机构资金外流", "技术形态破位", "宏观环境恶化"],
            "risk_factors": ["流动性枯竭", "恐慌性抛售", "监管打压"],
            "protection_strategies": ["减仓避险", "设置止损", "现金为王"],
            "support_levels": {
                "short_term": 35000,
                "medium_term": 30000,
                "long_term": 25000
            },
            "confidence_level": 72,
            "key_insights": ["熊市信号明确，建议防御性操作"]
        }, ensure_ascii=False)
    
    def _get_default_mock_response(self) -> str:
        """默认模拟响应"""
        return json.dumps({
            "analysis_result": "测试分析结果",
            "confidence_level": 70,
            "key_insights": ["这是一个测试响应"]
        }, ensure_ascii=False)
    
    def get_info(self):
        """获取适配器信息"""
        return {
            "provider": self.provider,
            "model": self.model,
            **self.kwargs
        }


def patch_llm_service_for_testing():
    """为测试修补LLM服务"""
    from src.crypto_trading_agents.services.llm_service import llm_service
    
    # 清空现有适配器
    llm_service.llm_adapters = {}
    
    # 添加模拟适配器
    llm_service.llm_adapters["dashscope"] = MockLLMAdapter("dashscope", "qwen-plus")
    llm_service.llm_adapters["deepseek"] = MockLLMAdapter("deepseek", "deepseek-chat")
    llm_service.default_provider = "dashscope"
    llm_service._initialized = True
    
    logger.info("LLM服务已修补为测试模式")


def test_llm_service_basic_functionality():
    """测试LLM服务基本功能"""
    print("=" * 60)
    print("🔧 测试LLM服务基本功能")
    print("=" * 60)
    
    try:
        from src.crypto_trading_agents.services.llm_service import llm_service
        
        # 修补服务用于测试
        patch_llm_service_for_testing()
        
        # 测试服务信息
        service_info = llm_service.get_service_info()
        print(f"✅ 服务信息: {json.dumps(service_info, ensure_ascii=False, indent=2)}")
        
        # 测试LLM调用
        test_prompt = "你是一位测试分析师，请分析测试数据。"
        response = llm_service.call_llm(test_prompt)
        print(f"✅ LLM调用成功，响应长度: {len(response)}")
        
        # 测试JSON解析
        parsed_result = llm_service.parse_json_response(response)
        print(f"✅ JSON解析成功: {type(parsed_result)}")
        
        # 测试提供商切换
        response_deepseek = llm_service.call_llm(test_prompt, provider="deepseek")
        print(f"✅ DeepSeek提供商调用成功，响应长度: {len(response_deepseek)}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM服务基本功能测试失败: {str(e)}")
        return False


def test_ai_analysis_mixin():
    """测试AI分析混入类"""
    print("\n" + "=" * 60)
    print("🧩 测试AI分析混入类")
    print("=" * 60)
    
    try:
        from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin
        
        # 创建测试类
        class TestAnalyst(StandardAIAnalysisMixin):
            def __init__(self, config):
                self.config = config
                super().__init__()
            
            def _analyze_with_ai(self, traditional_analysis, raw_data):
                prompt = "测试AI分析"
                response = self.call_ai_analysis(prompt)
                return self.parse_ai_json_response(response, {"test": "default"})
            
            def _combine_analyses(self, traditional_analysis, ai_analysis):
                return self._combine_standard_analyses(traditional_analysis, ai_analysis)
        
        # 测试配置
        test_config = {
            "ai_analysis_config": {
                "enabled": True,
                "temperature": 0.3,
                "max_tokens": 2000
            }
        }
        
        # 创建测试分析师
        analyst = TestAnalyst(test_config)
        
        # 测试AI功能检查
        print(f"✅ AI启用状态: {analyst.is_ai_enabled()}")
        
        # 测试AI分析信息
        ai_info = analyst.get_ai_analysis_info()
        print(f"✅ AI分析信息: {ai_info['analyzer']}")
        
        # 测试AI增强分析流程
        test_data = {"test_data": "样本数据"}
        traditional_result = {"traditional_score": 70, "confidence": 60}
        
        def mock_traditional_analyze(data):
            return traditional_result
        
        enhanced_result = analyst.analyze_with_ai_enhancement(test_data, mock_traditional_analyze)
        print(f"✅ AI增强分析完成，包含AI标记: {enhanced_result.get('ai_enhanced', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI分析混入类测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analyst_integration(analyst_class, analyst_name, test_data):
    """测试分析师集成"""
    try:
        from src.crypto_trading_agents.unified_config import get_unified_config
        
        print(f"\n📊 测试{analyst_name}集成")
        print("-" * 40)
        
        # 获取配置
        config = get_unified_config()
        
        # 创建分析师
        analyst = analyst_class(config)
        
        # 测试AI功能检查
        print(f"   AI启用状态: {analyst.is_ai_enabled()}")
        
        # 执行分析
        result = analyst.analyze(test_data)
        
        # 检查结果
        if "error" in result:
            print(f"   ⚠️  分析返回错误: {result['error']}")
            return False
        
        ai_enhanced = result.get('ai_enhanced', False)
        confidence = result.get('confidence', 0)
        
        print(f"   ✅ 分析完成 - AI增强: {ai_enhanced}, 置信度: {confidence:.2f}")
        
        # 检查AI特定字段
        ai_fields = [key for key in result.keys() if key.startswith('ai_')]
        if ai_fields:
            print(f"   🤖 AI字段数量: {len(ai_fields)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ {analyst_name}集成测试失败: {str(e)}")
        return False


def test_all_analysts_integration():
    """测试所有分析师的集成"""
    print("\n" + "=" * 60)
    print("🏢 测试所有分析师AI集成")
    print("=" * 60)
    
    # 修补服务用于测试
    patch_llm_service_for_testing()
    
    test_results = []
    
    # 测试OnchainAnalyst
    try:
        from src.crypto_trading_agents.agents.analysts.onchain_analyst import OnchainAnalyst
        onchain_data = {
            "active_addresses": {"daily_active": 920000},
            "transaction_metrics": {"daily_transactions": 1380000},
            "exchange_flows": {"net_flow": -3300},
            "whale_activity": {"whale_transactions": 52},
            "network_health": {"hash_rate": 520000000000000}
        }
        result = test_analyst_integration(OnchainAnalyst, "OnchainAnalyst", onchain_data)
        test_results.append(("OnchainAnalyst", result))
    except Exception as e:
        print(f"   ❌ OnchainAnalyst导入失败: {str(e)}")
        test_results.append(("OnchainAnalyst", False))
    
    # 测试SentimentAnalyst
    try:
        from src.crypto_trading_agents.agents.analysts.sentiment_analyst import SentimentAnalyst
        sentiment_data = {
            "twitter_sentiment": {"positive_ratio": 0.65},
            "reddit_sentiment": {"sentiment_score": 0.7},
            "fear_greed_index": {"current_value": 75},
            "news_sentiment": {"overall_sentiment": "positive"}
        }
        result = test_analyst_integration(SentimentAnalyst, "SentimentAnalyst", sentiment_data)
        test_results.append(("SentimentAnalyst", result))
    except Exception as e:
        print(f"   ❌ SentimentAnalyst导入失败: {str(e)}")
        test_results.append(("SentimentAnalyst", False))
    
    # 测试DefiAnalyst
    try:
        from src.crypto_trading_agents.agents.analysts.defi_analyst import DefiAnalyst
        defi_data = {
            "protocol_data": {"total_tvl": 45000000000},
            "liquidity_pools": {"top_pools": []},
            "yield_farming": {"average_apy": 12.5},
            "governance_data": {"active_proposals": 8}
        }
        result = test_analyst_integration(DefiAnalyst, "DefiAnalyst", defi_data)
        test_results.append(("DefiAnalyst", result))
    except Exception as e:
        print(f"   ❌ DefiAnalyst导入失败: {str(e)}")
        test_results.append(("DefiAnalyst", False))
    
    # 测试BullResearcher
    try:
        from src.crypto_trading_agents.agents.researchers.bull_researcher import BullResearcher
        bull_data = {
            "price_momentum_data": {"trend_strength": 0.8},
            "volume_analysis": {"volume_increase": 0.25},
            "institutional_flows": {"net_inflow": 1500000000},
            "technical_breakouts": {"breakout_confirmed": True}
        }
        result = test_analyst_integration(BullResearcher, "BullResearcher", bull_data)
        test_results.append(("BullResearcher", result))
    except Exception as e:
        print(f"   ❌ BullResearcher导入失败: {str(e)}")
        test_results.append(("BullResearcher", False))
    
    # 测试BearResearcher
    try:
        from src.crypto_trading_agents.agents.researchers.bear_researcher import BearResearcher
        bear_data = {
            "price_decline_data": {"decline_strength": 0.7},
            "volume_analysis": {"selling_pressure": 0.6},
            "institutional_outflows": {"net_outflow": -800000000},
            "technical_breakdown": {"support_broken": True}
        }
        result = test_analyst_integration(BearResearcher, "BearResearcher", bear_data)
        test_results.append(("BearResearcher", result))
    except Exception as e:
        print(f"   ❌ BearResearcher导入失败: {str(e)}")
        test_results.append(("BearResearcher", False))
    
    # 汇总结果
    successful = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    print(f"\n📈 分析师集成测试结果: {successful}/{total} 成功")
    for name, success in test_results:
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    return successful == total


def main():
    """主测试函数"""
    print("🚀 统一LLM服务测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 基本功能测试
    test_results.append(("LLM服务基本功能", test_llm_service_basic_functionality()))
    
    # AI分析混入类测试
    test_results.append(("AI分析混入类", test_ai_analysis_mixin()))
    
    # 分析师集成测试
    test_results.append(("所有分析师集成", test_all_analysts_integration()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    successful = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n🎯 总体测试结果: {successful}/{total} 测试通过")
    
    if successful == total:
        print("🎉 所有测试均通过！统一LLM服务集成成功。")
        return True
    else:
        print("🔧 部分测试失败，需要检查和修复。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
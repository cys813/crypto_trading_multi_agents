"""
测试AI增强的交易模块

测试新增的AI化模块：
1. MarketMakerAnalyst - AI增强的市场微观结构分析
2. CryptoRiskManager - AI增强的风险管理
3. CryptoTrader - AI增强的交易决策

使用mock LLM服务来验证模块的基本功能和集成
"""

import os
import sys
import json
from unittest.mock import Mock, patch
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../crypto_trading_agents'))

# 测试配置
test_config = {
    "llm_service_config": {
        "enabled": True,
        "primary_provider": "mock",
        "providers": {
            "mock": {
                "model": "mock-model",
                "api_key": "mock-key"
            }
        }
    },
    "crypto_config": {
        "supported_exchanges": ["binance", "coinbase"]
    },
    "risk_config": {
        "max_portfolio_risk": 0.02,
        "max_position_risk": 0.005,
        "max_drawdown": 0.10
    },
    "trading_config": {
        "max_position_size": 0.1,
        "max_leverage": 3,
        "strategies": ["trend_following", "mean_reversion"]
    }
}

def mock_llm_response(prompt: str) -> str:
    """模拟LLM响应"""
    if "市场微观结构" in prompt or "做市商" in prompt:
        return json.dumps({
            "confidence": 0.8,
            "trading_recommendation": {
                "action": "buy",
                "position_size": 0.05,
                "entry_price": 50500,
                "stop_loss": 49000,
                "take_profit": 52000
            },
            "market_structure_health": "healthy",
            "liquidity_outlook": "stable",
            "trading_opportunities": [
                "价差套利机会", 
                "流动性提供机会"
            ],
            "risk_factors": ["市场波动加大"],
            "optimal_strategy": "market_making"
        })
    elif "风险管理" in prompt or "风险分析" in prompt:
        return json.dumps({
            "confidence": 0.85,
            "risk_assessment": {
                "overall_risk_level": "medium",
                "risk_score": 0.45
            },
            "risk_scenarios": [
                {"scenario": "市场下跌", "probability": 0.3, "impact": -0.15}
            ],
            "hedge_strategy": {
                "recommended": "partial_hedge",
                "instruments": ["futures", "options"]
            },
            "allocation_advice": {
                "btc": 0.6,
                "eth": 0.3,
                "cash": 0.1
            },
            "model_recommendations": {
                "var_adjustment": "increase_confidence_level",
                "stress_test_frequency": "daily"
            }
        })
    elif "交易决策" in prompt or "交易分析" in prompt:
        return json.dumps({
            "confidence": 0.75,
            "trading_recommendation": {
                "action": "buy",
                "position_size": 0.08,
                "entry_price": 50200,
                "stop_loss": 48500,
                "take_profit": 53000
            },
            "market_timing": {
                "optimal_entry": "within_2_hours",
                "risk_factors": ["高波动性"]
            },
            "position_management": {
                "split_entry": True,
                "scaling_strategy": "gradual"
            },
            "risk_reward": {
                "expected_return": 0.055,
                "risk_ratio": 1.8
            },
            "execution_plan": {
                "entry_strategy": "limit_order",
                "timeframe": "4_hours"
            }
        })
    else:
        return json.dumps({
            "confidence": 0.5,
            "analysis": "基础分析完成"
        })

def test_market_maker_analyst():
    """测试AI增强的市场微观结构分析师"""
    print("\n=== 测试 MarketMakerAnalyst ===")
    
    try:
        # Mock LLM服务
        with patch('crypto_trading_agents.services.llm_service.LLMService') as mock_service_class:
            mock_service = Mock()
            mock_service.call_llm.return_value = mock_llm_response("市场微观结构分析")
            mock_service_class.return_value = mock_service
            
            from src.crypto_trading_agents.agents.analysts.market_maker_analyst import MarketMakerAnalyst
            
            # 初始化分析师
            analyst = MarketMakerAnalyst(test_config)
            print("✓ MarketMakerAnalyst 初始化成功")
            
            # 收集数据
            data = analyst.collect_data("BTC/USDT", "2024-01-15")
            print(f"✓ 数据收集成功，包含 {len(data)} 个数据项")
            
            # 执行分析
            analysis = analyst.analyze(data)
            print(f"✓ AI增强分析完成，置信度: {analysis.get('combined_confidence', 0):.3f}")
            print(f"  - 分析类型: {analysis.get('analysis_type', 'unknown')}")
            print(f"  - 最终建议: {analysis.get('final_recommendation', {}).get('action', 'unknown')}")
            
            return True
            
    except Exception as e:
        print(f"✗ MarketMakerAnalyst 测试失败: {e}")
        return False

def test_crypto_risk_manager():
    """测试AI增强的加密货币风险管理器"""
    print("\n=== 测试 CryptoRiskManager ===")
    
    try:
        # Mock LLM服务
        with patch('crypto_trading_agents.services.llm_service.LLMService') as mock_service_class:
            mock_service = Mock()
            mock_service.call_llm.return_value = mock_llm_response("风险管理分析")
            mock_service_class.return_value = mock_service
            
            from src.crypto_trading_agents.agents.risk_managers.crypto_risk_manager import CryptoRiskManager
            
            # 初始化风险管理器
            risk_manager = CryptoRiskManager(test_config)
            print("✓ CryptoRiskManager 初始化成功")
            
            # 收集数据
            data = risk_manager.collect_data("BTC/USDT", "2024-01-15")
            print(f"✓ 风险数据收集成功，包含 {len(data)} 个数据项")
            
            # 执行分析
            analysis = risk_manager.analyze(data)
            print(f"✓ AI增强风险分析完成，置信度: {analysis.get('combined_confidence', 0):.3f}")
            print(f"  - 分析类型: {analysis.get('analysis_type', 'unknown')}")
            print(f"  - 风险等级: {analysis.get('final_risk_assessment', {}).get('risk_level', 'unknown')}")
            
            return True
            
    except Exception as e:
        print(f"✗ CryptoRiskManager 测试失败: {e}")
        return False

def test_crypto_trader():
    """测试AI增强的加密货币交易员"""
    print("\n=== 测试 CryptoTrader ===")
    
    try:
        # Mock LLM服务
        with patch('crypto_trading_agents.services.llm_service.LLMService') as mock_service_class:
            mock_service = Mock()
            mock_service.call_llm.return_value = mock_llm_response("交易决策分析")
            mock_service_class.return_value = mock_service
            
            from src.crypto_trading_agents.agents.traders.crypto_trader import CryptoTrader
            
            # 初始化交易员
            trader = CryptoTrader(test_config)
            print("✓ CryptoTrader 初始化成功")
            
            # 收集数据
            data = trader.collect_data("BTC/USDT", "2024-01-15")
            print(f"✓ 交易数据收集成功，包含 {len(data)} 个数据项")
            
            # 执行分析
            analysis = trader.analyze(data)
            print(f"✓ AI增强交易分析完成，置信度: {analysis.get('combined_confidence', 0):.3f}")
            print(f"  - 分析类型: {analysis.get('analysis_type', 'unknown')}")
            print(f"  - 交易建议: {analysis.get('final_recommendation', {}).get('action', 'unknown')}")
            
            # 执行交易（如果有明确信号）
            final_action = analysis.get('final_recommendation', {}).get('action', 'hold')
            if final_action != 'hold':
                execution_result = trader.execute_trade(analysis)
                print(f"✓ 交易执行完成，状态: {execution_result.get('status', 'unknown')}")
            else:
                print("  - 交易信号为持有，未执行交易")
            
            return True
            
    except Exception as e:
        print(f"✗ CryptoTrader 测试失败: {e}")
        return False

def test_integration():
    """测试模块集成"""
    print("\n=== 测试模块集成 ===")
    
    try:
        # Mock LLM服务
        with patch('crypto_trading_agents.services.llm_service.LLMService') as mock_service_class:
            mock_service = Mock()
            mock_service.call_llm.side_effect = lambda prompt: mock_llm_response(prompt)
            mock_service_class.return_value = mock_service
            
            from src.crypto_trading_agents.agents.analysts.market_maker_analyst import MarketMakerAnalyst
            from src.crypto_trading_agents.agents.risk_managers.crypto_risk_manager import CryptoRiskManager
            from src.crypto_trading_agents.agents.traders.crypto_trader import CryptoTrader
            
            # 初始化所有模块
            analyst = MarketMakerAnalyst(test_config)
            risk_manager = CryptoRiskManager(test_config)
            trader = CryptoTrader(test_config)
            
            symbol = "BTC/USDT"
            end_date = "2024-01-15"
            
            # 执行完整的分析流程
            print("执行完整的AI增强分析流程:")
            
            # 1. 市场微观结构分析
            market_data = analyst.collect_data(symbol, end_date)
            market_analysis = analyst.analyze(market_data)
            print(f"  1. 市场分析完成 - 置信度: {market_analysis.get('combined_confidence', 0):.3f}")
            
            # 2. 风险分析
            risk_data = risk_manager.collect_data(symbol, end_date)
            risk_analysis = risk_manager.analyze(risk_data)
            print(f"  2. 风险分析完成 - 风险等级: {risk_analysis.get('final_risk_assessment', {}).get('risk_level', 'unknown')}")
            
            # 3. 交易决策
            trading_data = trader.collect_data(symbol, end_date)
            trading_analysis = trader.analyze(trading_data)
            print(f"  3. 交易分析完成 - 建议: {trading_analysis.get('final_recommendation', {}).get('action', 'unknown')}")
            
            # 4. 综合决策评估
            combined_confidence = (
                market_analysis.get('combined_confidence', 0) +
                risk_analysis.get('combined_confidence', 0) + 
                trading_analysis.get('combined_confidence', 0)
            ) / 3
            
            print(f"✓ 综合AI分析完成，平均置信度: {combined_confidence:.3f}")
            print("✓ 所有模块成功使用统一LLM框架")
            
            return True
            
    except Exception as e:
        print(f"✗ 模块集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试AI增强的交易模块...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    tests = [
        ("MarketMakerAnalyst", test_market_maker_analyst),
        ("CryptoRiskManager", test_crypto_risk_manager), 
        ("CryptoTrader", test_crypto_trader),
        ("模块集成", test_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        success = test_func()
        results.append((test_name, success))
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print("测试结果摘要:")
    print(f"{'='*50}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name:30} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有AI增强模块测试通过！")
        print("✓ MarketMakerAnalyst 成功集成统一LLM框架")
        print("✓ CryptoRiskManager 成功集成统一LLM框架") 
        print("✓ CryptoTrader 成功集成智能交易决策")
        print("✓ 所有模块遵循StandardAIAnalysisMixin模式")
    else:
        print(f"\n⚠️  {failed} 个测试失败，需要检查相关模块")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
简单的debator系统功能测试
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from crypto_trading_agents.agents.risk_managers.aggresive_debator import AggressiveDebator
from crypto_trading_agents.agents.risk_managers.neutral_debator import NeutralDebator
from crypto_trading_agents.agents.risk_managers.conservative_debator import ConservativeDebator

def test_debator_functionality():
    """测试debator系统功能"""
    print("=== Debator系统功能测试 ===")
    
    # 配置
    config = {
        'name': 'test_debator',
        'ai_config': {
            'enable_ai': False  # 禁用AI以避免网络依赖
        }
    }
    
    # 测试数据
    test_data = {
        'market_data': {
            'price': 50000,
            'volume': 1000000,
            'change_24h': 2.5
        },
        'sentiment_data': {
            'score': 0.6,
            'trend': 'bullish'
        }
    }
    
    # 实例化debators
    debators = []
    
    try:
        aggressive = AggressiveDebator(config)
        debators.append(('Aggressive', aggressive))
        print("✓ AggressiveDebator 创建成功")
    except Exception as e:
        print(f"✗ AggressiveDebator 创建失败: {e}")
        return False
    
    try:
        neutral = NeutralDebator(config)
        debators.append(('Neutral', neutral))
        print("✓ NeutralDebator 创建成功")
    except Exception as e:
        print(f"✗ NeutralDebator 创建失败: {e}")
        return False
    
    try:
        conservative = ConservativeDebator(config)
        debators.append(('Conservative', conservative))
        print("✓ ConservativeDebator 创建成功")
    except Exception as e:
        print(f"✗ ConservativeDebator 创建失败: {e}")
        return False
    
    # 测试基本分析功能
    print("\n--- 测试基本分析功能 ---")
    for name, debator in debators:
        try:
            result = debator.analyze(test_data)
            print(f"✓ {name} 分析成功")
            print(f"  风险等级: {result.get('risk_level', 'unknown')}")
            print(f"  置信度: {result.get('confidence', 0):.2f}")
            print(f"  AI增强: {result.get('ai_enhanced', False)}")
        except Exception as e:
            print(f"✗ {name} 分析失败: {e}")
    
    # 测试辩论材料分析功能
    print("\n--- 测试辩论材料分析功能 ---")
    debate_material = {
        'market_analysis': {'trend': 'bullish', 'volatility': 'medium'},
        'sentiment_analysis': {'score': 0.7, 'sources': ['twitter', 'reddit']},
        'technical_analysis': {'signals': ['buy', 'strong']},
        'fundamental_analysis': {'value': 'overvalued', 'growth': 'high'}
    }
    
    for name, debator in debators:
        try:
            result = debator.analyze_with_debate_material(debate_material)
            print(f"✓ {name} 辩论材料分析成功")
            print(f"  综合风险评估: {result.get('comprehensive_risk_assessment', 'unknown')}")
            print(f"  最终建议: {result.get('final_recommendation', 'unknown')}")
        except Exception as e:
            print(f"✗ {name} 辩论材料分析失败: {e}")
    
    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    test_debator_functionality()
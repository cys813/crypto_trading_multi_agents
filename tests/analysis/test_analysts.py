#!/usr/bin/env python3
"""
测试技术分析师使用新的交易数据服务
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../crypto_trading_agents'))

def test_technical_analyst():
    """测试技术分析师"""
    print("=== 测试技术分析师 ===")
    
    try:
        from agents.analysts.technical_analyst import TechnicalAnalyst
        
        analyst = TechnicalAnalyst({})
        symbol = "BTC/USDT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 测试数据收集
        data = analyst.collect_data(symbol, end_date)
        print(f"✅ 技术分析师数据收集成功")
        print(f"   - 数据类型: {list(data.keys())}")
        
        # 测试分析执行
        analysis = analyst.analyze(symbol, end_date)
        print(f"✅ 技术分析师分析执行成功")
        print(f"   - 分析结果包含: {list(analysis.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 技术分析师测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bull_researcher():
    """测试看涨分析师"""
    print("\n=== 测试看涨分析师 ===")
    
    try:
        from agents.researchers.bull_researcher import BullResearcher
        
        researcher = BullResearcher({})
        symbol = "BTC/USDT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 测试看涨信号分析
        signals = researcher.trading_data_bull_signals(symbol, end_date)
        print(f"✅ 看涨分析师信号分析成功")
        print(f"   - 信号强度: {signals.get('signal_strength', 'N/A')}")
        print(f"   - 建议操作: {signals.get('action', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 看涨分析师测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bear_researcher():
    """测试看跌分析师"""
    print("\n=== 测试看跌分析师 ===")
    
    try:
        from agents.researchers.bear_researcher import BearResearcher
        
        researcher = BearResearcher({})
        symbol = "BTC/USDT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 测试看跌信号分析
        signals = researcher.trading_data_bear_signals(symbol, end_date)
        print(f"✅ 看跌分析师信号分析成功")
        print(f"   - 信号强度: {signals.get('signal_strength', 'N/A')}")
        print(f"   - 建议操作: {signals.get('action', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 看跌分析师测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试新的统一交易数据系统...")
    print("=" * 50)
    
    results = []
    
    # 运行所有测试
    results.append(test_technical_analyst())
    results.append(test_bull_researcher())
    results.append(test_bear_researcher())
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"✅ 通过: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 所有测试通过！新的统一交易数据系统工作正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit(main())
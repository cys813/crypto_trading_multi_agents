#!/usr/bin/env python3
"""
测试新的统一交易数据服务
验证技术分析师、看涨分析师、看跌分析师是否都能正常工作
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto_trading_agents.crypto_trading_agents.services.trading_data_service import TradingDataService
from crypto_trading_agents.crypto_trading_agents.agents.analysts.technical_analyst import TechnicalAnalyst
from crypto_trading_agents.crypto_trading_agents.agents.researchers.bull_researcher import BullResearcher
from crypto_trading_agents.crypto_trading_agents.agents.researchers.bear_researcher import BearResearcher

def test_trading_data_service():
    """测试交易数据服务"""
    print("=== 测试交易数据服务 ===")
    
    service = TradingDataService()
    
    # 测试获取交易数据
    symbol = "BTC/USDT"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        data = service.get_trading_data(symbol, end_date)
        print(f"✅ 成功获取 {symbol} 的交易数据")
        print(f"   - 4小时数据点数: {len(data.get('4h', []))}")
        print(f"   - 1小时数据点数: {len(data.get('1h', []))}")
        print(f"   - 15分钟数据点数: {len(data.get('15m', []))}")
        return True
    except Exception as e:
        print(f"❌ 交易数据服务测试失败: {e}")
        return False

def test_technical_analyst():
    """测试技术分析师"""
    print("\n=== 测试技术分析师 ===")
    
    try:
        analyst = TechnicalAnalyst()
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
        return False

def test_bull_researcher():
    """测试看涨分析师"""
    print("\n=== 测试看涨分析师 ===")
    
    try:
        researcher = BullResearcher()
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
        return False

def test_bear_researcher():
    """测试看跌分析师"""
    print("\n=== 测试看跌分析师 ===")
    
    try:
        researcher = BearResearcher()
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
        return False

def main():
    """主测试函数"""
    print("开始测试新的统一交易数据系统...")
    print("=" * 50)
    
    results = []
    
    # 运行所有测试
    results.append(test_trading_data_service())
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
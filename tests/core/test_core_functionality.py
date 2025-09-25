#!/usr/bin/env python3
"""
简单测试统一交易数据架构
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../crypto_trading_agents'))

def test_trading_data_service():
    """测试交易数据服务"""
    print("=== 测试交易数据服务 ===")
    
    try:
        from services.trading_data_service import TradingDataService
        
        service = TradingDataService({})
        symbol = "BTC/USDT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 测试获取交易数据
        data = service.get_trading_data(symbol, end_date)
        print(f"✅ 成功获取 {symbol} 的交易数据")
        print(f"   - 数据时间框架: {list(data.keys())}")
        print(f"   - 数据点数: {sum(len(v) for v in data.values())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 交易数据服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_imports():
    """测试直接导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        # 测试交易数据服务导入
        from services.trading_data_service import TradingDataService
        print("✅ TradingDataService 导入成功")
        
        # 测试AI分析混入类导入
        from services.ai_analysis_mixin import StandardAIAnalysisMixin
        print("✅ StandardAIAnalysisMixin 导入成功")
        
        # 测试LLM服务导入
        from services.llm_service import initialize_llm_service
        print("✅ LLM服务导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    try:
        from services.trading_data_service import TradingDataService
        
        # 测试服务实例化
        service = TradingDataService({})
        print("✅ 交易数据服务实例化成功")
        
        # 测试基本方法
        symbol = "BTC/USDT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 测试数据获取
        data = service.get_trading_data(symbol, end_date)
        print(f"✅ 数据获取功能正常")
        
        # 测试数据结构
        if isinstance(data, dict):
            print("✅ 返回数据结构正确")
        else:
            print("❌ 返回数据结构错误")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试统一交易数据架构...")
    print("=" * 50)
    
    results = []
    
    # 运行所有测试
    results.append(test_direct_imports())
    results.append(test_trading_data_service())
    results.append(test_basic_functionality())
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"✅ 通过: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 核心功能测试通过！统一交易数据架构工作正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit(main())
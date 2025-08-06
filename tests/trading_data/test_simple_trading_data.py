#!/usr/bin/env python3
"""
简单测试交易数据服务
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
        print(f"   - 4小时数据点数: {len(data.get('4h', []))}")
        print(f"   - 1小时数据点数: {len(data.get('1h', []))}")
        print(f"   - 15分钟数据点数: {len(data.get('15m', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 交易数据服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trading_data_service()
    if success:
        print("\n🎉 交易数据服务测试通过！")
    else:
        print("\n⚠️  交易数据服务测试失败")
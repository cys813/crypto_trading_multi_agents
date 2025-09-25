#!/usr/bin/env python3
"""
简单测试分层数据功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_sources.exchange_data_sources import ExchangeManager
from src.database.models import layered_data_storage

def test_layered_data():
    """测试分层数据获取"""
    print("测试分层数据获取功能...")
    
    # 创建交易所管理器
    exchange_manager = ExchangeManager()
    
    # 测试获取BTC/USDT的分层数据
    symbol = "BTC/USDT"
    print(f"获取 {symbol} 的30天分层数据...")
    
    try:
        # 获取分层数据
        layered_data = exchange_manager.get_layered_ohlcv_30d(symbol)
        
        if "error" in layered_data:
            print(f"获取数据失败: {layered_data['error']}")
            return False
        
        # 检查数据结构
        layers = layered_data.get("layers", {})
        print(f"成功获取 {len(layers)} 层数据:")
        
        for layer_name, layer_info in layers.items():
            data_count = len(layer_info.get("data", []))
            timeframe = layer_info.get("timeframe", "unknown")
            print(f"  - {layer_name}: {data_count} 个数据点, 时间框架: {timeframe}")
        
        # 检查数据质量
        quality = layered_data.get("quality", {})
        print(f"数据质量评分: {quality.get('overall_score', 0):.2f}")
        print(f"完整性: {quality.get('completeness', 0):.2f}")
        print(f"连续性: {quality.get('continuity', 0):.2f}")
        
        # 测试数据存储
        print("\n测试数据存储...")
        storage_success = layered_data_storage.save_layered_data(symbol, layered_data)
        if storage_success:
            print("数据存储成功")
            
            # 测试数据读取
            loaded_data = layered_data_storage.load_latest_layered_data(symbol)
            if loaded_data:
                print("数据读取成功")
                print(f"缓存的数据层数: {len(loaded_data.get('layers', {}))}")
            else:
                print("数据读取失败")
        else:
            print("数据存储失败")
        
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_layered_data()
    if success:
        print("\n✅ 分层数据功能测试通过!")
    else:
        print("\n❌ 分层数据功能测试失败!")
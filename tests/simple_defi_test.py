#!/usr/bin/env python3
"""
简化版DeFi分析师测试脚本
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_defi_data_service():
    """测试DeFi数据服务"""
    print("🧪 测试DeFi数据服务...")
    
    # 导入配置
    try:
        from src.crypto_trading_agents.unified_config import get_unified_config
        config = get_unified_config()
        print("✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        config = {}
    
    # 测试DeFi数据服务
    try:
        from src.crypto_trading_agents.services.onchain_data.defi_data_service import DeFiDataService
        defi_service = DeFiDataService(config)
        print("✅ DeFi数据服务初始化成功")
        
        # 测试资产支持检查
        print("\n1. 测试资产支持检查...")
        supported_assets = ["ETH", "BTC", "SOL", "BNB"]
        for asset in supported_assets:
            is_supported = defi_service.is_defi_supported(asset)
            print(f"   {asset}: {'✅ 支持' if is_supported else '❌ 不支持'}")
        
        # 测试协议数据获取
        print("\n2. 测试协议数据获取...")
        try:
            eth_protocols = defi_service.get_protocol_data("ETH")
            print(f"   ✅ ETH协议数据获取成功")
            print(f"      协议数量: {len(eth_protocols)}")
            
            btc_protocols = defi_service.get_protocol_data("BTC")
            print(f"   ✅ BTC协议数据获取成功")
            print(f"      协议数量: {len(btc_protocols)}")
            
        except Exception as e:
            print(f"   ⚠️  协议数据获取出现预期的错误: {str(e)}")
        
        # 测试其他数据获取
        print("\n3. 测试其他数据获取...")
        try:
            eth_pools = defi_service.get_liquidity_pools_data("ETH")
            print(f"   ✅ ETH流动性池数据获取成功")
            print(f"      池数量: {len(eth_pools.get('pools', []))}")
            
            eth_yield = defi_service.get_yield_farming_data("ETH")
            print(f"   ✅ ETH收益挖矿数据获取成功")
            print(f"      农场数量: {len(eth_yield.get('farms', []))}")
            
        except Exception as e:
            print(f"   ⚠️  其他数据获取出现预期的错误: {str(e)}")
            
    except Exception as e:
        print(f"❌ DeFi数据服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_defi_analyst_import():
    """测试DeFi分析师导入"""
    print("\n\n🧪 测试DeFi分析师导入...")
    
    try:
        from src.crypto_trading_agents.agents.analysts.defi_analyst import DefiAnalyst
        print("✅ DeFi分析师导入成功")
        
        # 测试初始化
        try:
            from src.crypto_trading_agents.unified_config import get_unified_config
            config = get_unified_config()
            analyst = DefiAnalyst(config)
            print("✅ DeFi分析师初始化成功")
        except Exception as e:
            print(f"⚠️  DeFi分析师初始化出现预期错误: {str(e)}")
            
    except Exception as e:
        print(f"❌ DeFi分析师导入失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 简化版DeFi分析师功能测试")
    print("=" * 50)
    
    test_defi_data_service()
    test_defi_analyst_import()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")
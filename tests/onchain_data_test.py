#!/usr/bin/env python3
"""
链上数据服务测试脚本
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.crypto_trading_agents.services.onchain_data.onchain_data_service import OnchainDataService
from src.crypto_trading_agents.unified_config import get_unified_config

def test_onchain_data_service():
    """测试链上数据服务"""
    print("🧪 测试链上数据服务...")
    
    # 获取配置
    config = get_unified_config()
    
    # 初始化链上数据服务
    onchain_service = OnchainDataService(config)
    
    # 测试获取活跃地址数据
    print("\n1. 测试获取活跃地址数据...")
    try:
        active_addresses = onchain_service.get_active_addresses("BTC", "bitcoin", "2025-08-07")
        print(f"   ✅ 活跃地址数据获取成功: {active_addresses.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 活跃地址数据获取失败: {str(e)}")
    
    # 测试获取交易指标数据
    print("\n2. 测试获取交易指标数据...")
    try:
        tx_metrics = onchain_service.get_transaction_metrics("BTC", "bitcoin", "2025-08-07")
        print(f"   ✅ 交易指标数据获取成功: {tx_metrics.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 交易指标数据获取失败: {str(e)}")
    
    # 测试获取交易所流量数据
    print("\n3. 测试获取交易所流量数据...")
    try:
        exchange_flows = onchain_service.get_exchange_flows("BTC", "bitcoin", "2025-08-07")
        print(f"   ✅ 交易所流量数据获取成功: {exchange_flows.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 交易所流量数据获取失败: {str(e)}")
    
    # 测试获取巨鲸活动数据
    print("\n4. 测试获取巨鲸活动数据...")
    try:
        whale_activity = onchain_service.get_whale_activity("BTC", "bitcoin", "2025-08-07")
        print(f"   ✅ 巨鲸活动数据获取成功: {whale_activity.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 巨鲸活动数据获取失败: {str(e)}")
    
    # 测试获取网络健康度数据
    print("\n5. 测试获取网络健康度数据...")
    try:
        network_health = onchain_service.get_network_health("BTC", "bitcoin", "2025-08-07")
        print(f"   ✅ 网络健康度数据获取成功: {network_health.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 网络健康度数据获取失败: {str(e)}")
    
    # 测试获取DeFi指标数据
    print("\n6. 测试获取DeFi指标数据...")
    try:
        defi_metrics = onchain_service.get_defi_metrics("ETH", "ethereum", "2025-08-07")
        print(f"   ✅ DeFi指标数据获取成功: {defi_metrics.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ DeFi指标数据获取失败: {str(e)}")
    
    # 测试获取持有者分布数据
    print("\n7. 测试获取持有者分布数据...")
    try:
        holder_dist = onchain_service.get_holder_distribution("BTC", "bitcoin", "2025-08-07")
        print(f"   ✅ 持有者分布数据获取成功: {holder_dist.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 持有者分布数据获取失败: {str(e)}")

def test_onchain_analyst_integration():
    """测试链上分析师集成"""
    print("\n\n🧪 测试链上分析师集成...")
    
    # 获取配置
    config = get_unified_config()
    
    # 导入链上分析师
    from src.crypto_trading_agents.agents.analysts.onchain_analyst import OnchainAnalyst
    
    # 初始化链上分析师
    analyst = OnchainAnalyst(config)
    
    # 测试收集数据
    print("\n1. 测试收集BTC链上数据...")
    try:
        data = analyst.collect_data("BTC/USDT", "2025-08-07")
        print(f"   ✅ BTC链上数据收集成功")
        print(f"      活跃地址来源: {data.get('active_addresses', {}).get('source', 'unknown')}")
        print(f"      交易指标来源: {data.get('transaction_metrics', {}).get('source', 'unknown')}")
        print(f"      交易所流量来源: {data.get('exchange_flows', {}).get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ BTC链上数据收集失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 链上数据服务测试")
    print("=" * 50)
    
    test_onchain_data_service()
    test_onchain_analyst_integration()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")
#!/usr/bin/env python3
"""
TON链数据服务测试脚本
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.crypto_trading_agents.services.onchain_data.ton_data_service import TonDataService
from src.crypto_trading_agents.unified_config import get_unified_config

def test_ton_data_service():
    """测试TON数据服务"""
    print("🧪 测试TON链数据服务...")
    
    # 获取配置
    config = get_unified_config()
    
    # 启用TON服务
    if "apis" not in config:
        config["apis"] = {}
    if "data" not in config["apis"]:
        config["apis"]["data"] = {}
    if "onchain_data" not in config["apis"]["data"]:
        config["apis"]["data"]["onchain_data"] = {}
    
    config["apis"]["data"]["onchain_data"]["ton"] = {
        "enabled": True,
        "toncenter": {
            "enabled": True,
            "api_key": None  # 使用公开API
        },
        "tonanalytics": {
            "enabled": False,  # 需要API密钥
            "api_key": None
        }
    }
    
    # 初始化TON数据服务
    ton_service = TonDataService(config)
    
    # 测试获取网络健康度数据
    print("\n1. 测试获取TON网络健康度数据...")
    try:
        network_health = ton_service.get_network_health("TON", 30)
        print(f"   ✅ TON网络健康度数据获取成功: {network_health.get('source', 'unknown')}")
        if network_health.get('source') == 'mock':
            print(f"      验证者数量: {network_health.get('validator_count', 'N/A')}")
            print(f"      网络健康评分: {network_health.get('network_health_score', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON网络健康度数据获取失败: {str(e)}")
    
    # 测试获取活跃地址数据
    print("\n2. 测试获取TON活跃地址数据...")
    try:
        active_addresses = ton_service.get_active_addresses("TON", 30)
        print(f"   ✅ TON活跃地址数据获取成功: {active_addresses.get('source', 'unknown')}")
        if active_addresses.get('source') == 'mock':
            print(f"      日活跃地址: {active_addresses.get('daily_active', 'N/A')}")
            print(f"      增长率: {active_addresses.get('growth_rate_7d', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON活跃地址数据获取失败: {str(e)}")
    
    # 测试获取交易指标数据
    print("\n3. 测试获取TON交易指标数据...")
    try:
        tx_metrics = ton_service.get_transaction_metrics("TON", 30)
        print(f"   ✅ TON交易指标数据获取成功: {tx_metrics.get('source', 'unknown')}")
        if tx_metrics.get('source') == 'mock':
            print(f"      日交易量: {tx_metrics.get('daily_transactions', 'N/A')}")
            print(f"      平均手续费: {tx_metrics.get('average_fee', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON交易指标数据获取失败: {str(e)}")
    
    # 测试获取验证者指标数据
    print("\n4. 测试获取TON验证者指标数据...")
    try:
        validator_metrics = ton_service.get_validator_metrics("TON")
        print(f"   ✅ TON验证者指标数据获取成功: {validator_metrics.get('source', 'unknown')}")
        if validator_metrics.get('source') == 'mock':
            print(f"      验证者总数: {validator_metrics.get('validator_count', 'N/A')}")
            print(f"      参与率: {validator_metrics.get('election_participation', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON验证者指标数据获取失败: {str(e)}")
    
    # 测试获取巨鲸活动数据
    print("\n5. 测试获取TON巨鲸活动数据...")
    try:
        whale_activity = ton_service.get_whale_activity("TON", 30)
        print(f"   ✅ TON巨鲸活动数据获取成功: {whale_activity.get('source', 'unknown')}")
        if whale_activity.get('source') == 'mock':
            print(f"      巨鲸集中度: {whale_activity.get('whale_concentration', 'N/A')}")
            print(f"      净流量: {whale_activity.get('whale_net_flow', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON巨鲸活动数据获取失败: {str(e)}")
    
    # 测试获取DeFi指标数据
    print("\n6. 测试获取TON DeFi指标数据...")
    try:
        defi_metrics = ton_service.get_defi_metrics("TON", 30)
        print(f"   ✅ TON DeFi指标数据获取成功: {defi_metrics.get('source', 'unknown')}")
        if defi_metrics.get('source') == 'mock':
            print(f"      TVL: {defi_metrics.get('total_value_locked', 'N/A')}")
            print(f"      DeFi增长率: {defi_metrics.get('defi_growth_30d', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON DeFi指标数据获取失败: {str(e)}")

def test_ton_integration_with_unified_service():
    """测试TON与统一链上数据服务的集成"""
    print("\n\n🧪 测试TON与统一链上数据服务集成...")
    
    # 获取配置
    config = get_unified_config()
    
    # 启用TON服务
    if "apis" not in config:
        config["apis"] = {}
    if "data" not in config["apis"]:
        config["apis"]["data"] = {}
    if "onchain_data" not in config["apis"]["data"]:
        config["apis"]["data"]["onchain_data"] = {}
    
    config["apis"]["data"]["onchain_data"]["ton"] = {
        "enabled": True,
        "toncenter": {
            "enabled": True,
            "api_key": None  # 使用公开API
        },
        "tonanalytics": {
            "enabled": False,
            "api_key": None
        }
    }
    
    # 初始化统一链上数据服务
    from src.crypto_trading_agents.services.onchain_data.onchain_data_service import OnchainDataService
    unified_service = OnchainDataService(config)
    
    # 测试TON数据获取
    print("\n1. 测试通过统一服务获取TON活跃地址...")
    try:
        active_addresses = unified_service.get_active_addresses("TON", "ton", "2025-08-08")
        print(f"   ✅ TON活跃地址数据获取成功: {active_addresses.get('source', 'unknown')}")
        if 'ton_data' in active_addresses:
            ton_data = active_addresses['ton_data']
            print(f"      日活跃地址: {ton_data.get('daily_active', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON活跃地址数据获取失败: {str(e)}")
    
    # 测试TON网络健康度获取
    print("\n2. 测试通过统一服务获取TON网络健康度...")
    try:
        network_health = unified_service.get_network_health("TON", "ton", "2025-08-08")
        print(f"   ✅ TON网络健康度数据获取成功: {network_health.get('source', 'unknown')}")
        if 'ton_data' in network_health:
            ton_data = network_health['ton_data']
            print(f"      验证者数量: {ton_data.get('validator_count', 'N/A')}")
    except Exception as e:
        print(f"   ❌ TON网络健康度数据获取失败: {str(e)}")
    
    # 测试传统区块链数据获取(对比测试)
    print("\n3. 测试传统区块链数据获取(BTC)...")
    try:
        btc_active_addresses = unified_service.get_active_addresses("BTC", "bitcoin", "2025-08-08")
        print(f"   ✅ BTC活跃地址数据获取成功: {btc_active_addresses.get('source', 'unknown')}")
        if btc_active_addresses.get('source') == 'mock':
            print(f"      日活跃地址: {btc_active_addresses.get('daily_active', 'N/A')}")
    except Exception as e:
        print(f"   ❌ BTC活跃地址数据获取失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 TON链数据服务测试")
    print("=" * 50)
    
    test_ton_data_service()
    test_ton_integration_with_unified_service()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")
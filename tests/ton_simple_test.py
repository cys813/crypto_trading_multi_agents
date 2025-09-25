#!/usr/bin/env python3
"""
TON链数据服务简化测试脚本
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_ton_imports():
    """测试TON模块导入"""
    print("🧪 测试TON模块导入...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.ton_clients import TONCenterClient, TONAnalyticsClient
        print("   ✅ TON客户端导入成功")
    except ImportError as e:
        print(f"   ❌ TON客户端导入失败: {str(e)}")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.ton_data_service import TonDataService
        print("   ✅ TON数据服务导入成功")
    except ImportError as e:
        print(f"   ❌ TON数据服务导入失败: {str(e)}")

def test_ton_client_initialization():
    """测试TON客户端初始化"""
    print("\n🧪 测试TON客户端初始化...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.ton_clients import TONCenterClient
        client = TONCenterClient()
        print("   ✅ TONCenter客户端初始化成功")
        print(f"      基础URL: {client.base_url}")
        print(f"      是否有API密钥: {client.api_key is not None}")
    except Exception as e:
        print(f"   ❌ TONCenter客户端初始化失败: {str(e)}")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.ton_clients import TONAnalyticsClient
        client = TONAnalyticsClient()
        print("   ✅ TONAnalytics客户端初始化成功")
        print(f"      基础URL: {client.base_url}")
        print(f"      是否有API密钥: {client.api_key is not None}")
    except Exception as e:
        print(f"   ❌ TONAnalytics客户端初始化失败: {str(e)}")

def test_ton_service_initialization():
    """测试TON服务初始化"""
    print("\n🧪 测试TON服务初始化...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.ton_data_service import TonDataService
        # 创建一个简单的配置
        config = {
            "apis": {
                "data": {
                    "onchain_data": {
                        "ton": {
                            "enabled": True,
                            "toncenter": {
                                "enabled": True,
                                "api_key": None
                            },
                            "tonanalytics": {
                                "enabled": False,
                                "api_key": None
                            }
                        }
                    }
                }
            }
        }
        
        service = TonDataService(config)
        print("   ✅ TON数据服务初始化成功")
        print(f"      是否有TONCenter客户端: {service.toncenter_client is not None}")
        print(f"      是否有TONAnalytics客户端: {service.tonanalytics_client is not None}")
    except Exception as e:
        print(f"   ❌ TON数据服务初始化失败: {str(e)}")

def test_mock_data_generation():
    """测试模拟数据生成"""
    print("\n🧪 测试模拟数据生成...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.ton_data_service import TonDataService
        # 创建一个简单的配置
        config = {
            "apis": {
                "data": {
                    "onchain_data": {
                        "ton": {
                            "enabled": True,
                            "toncenter": {
                                "enabled": False,  # 禁用实际客户端以测试模拟数据
                                "api_key": None
                            },
                            "tonanalytics": {
                                "enabled": False,
                                "api_key": None
                            }
                        }
                    }
                }
            }
        }
        
        service = TonDataService(config)
        
        # 测试网络健康度数据生成
        network_health = service.get_network_health("TON", 30)
        print("   ✅ 网络健康度模拟数据生成成功")
        print(f"      数据来源: {network_health.get('source')}")
        print(f"      验证者数量: {network_health.get('validator_count')}")
        
        # 测试活跃地址数据生成
        active_addresses = service.get_active_addresses("TON", 30)
        print("   ✅ 活跃地址模拟数据生成成功")
        print(f"      数据来源: {active_addresses.get('source')}")
        print(f"      日活跃地址: {active_addresses.get('daily_active')}")
        
        # 测试交易指标数据生成
        tx_metrics = service.get_transaction_metrics("TON", 30)
        print("   ✅ 交易指标模拟数据生成成功")
        print(f"      数据来源: {tx_metrics.get('source')}")
        print(f"      日交易量: {tx_metrics.get('daily_transactions')}")
        
    except Exception as e:
        print(f"   ❌ 模拟数据生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 TON链数据服务简化测试")
    print("=" * 50)
    
    test_ton_imports()
    test_ton_client_initialization()
    test_ton_service_initialization()
    test_mock_data_generation()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")
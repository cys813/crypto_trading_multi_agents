#!/usr/bin/env python3
"""
Solana链数据服务测试脚本
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_solana_imports():
    """测试Solana模块导入"""
    print("🧪 测试Solana模块导入...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.solana_clients import SolanaRPCClient, SolscanClient, HeliusClient
        print("   ✅ Solana客户端导入成功")
    except ImportError as e:
        print(f"   ❌ Solana客户端导入失败: {str(e)}")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.solana_data_service import SolanaDataService
        print("   ✅ Solana数据服务导入成功")
    except ImportError as e:
        print(f"   ❌ Solana数据服务导入失败: {str(e)}")

def test_solana_client_initialization():
    """测试Solana客户端初始化"""
    print("\n🧪 测试Solana客户端初始化...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.solana_clients import SolanaRPCClient
        client = SolanaRPCClient()
        print("   ✅ Solana RPC客户端初始化成功")
        print(f"      RPC URL: {client.rpc_url}")
    except Exception as e:
        print(f"   ❌ Solana RPC客户端初始化失败: {str(e)}")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.solana_clients import SolscanClient
        client = SolscanClient()
        print("   ✅ Solscan客户端初始化成功")
        print(f"      基础URL: {client.base_url}")
        print(f"      是否有API密钥: {client.api_key is not None}")
    except Exception as e:
        print(f"   ❌ Solscan客户端初始化失败: {str(e)}")

def test_solana_service_initialization():
    """测试Solana服务初始化"""
    print("\n🧪 测试Solana服务初始化...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.solana_data_service import SolanaDataService
        # 创建一个简单的配置
        config = {
            "apis": {
                "data": {
                    "onchain_data": {
                        "solana": {
                            "enabled": True,
                            "rpc": {
                                "enabled": True,
                                "url": "https://api.mainnet-beta.solana.com"
                            },
                            "solscan": {
                                "enabled": False,
                                "api_key": None
                            },
                            "helius": {
                                "enabled": False,
                                "api_key": None
                            }
                        }
                    }
                }
            }
        }
        
        service = SolanaDataService(config)
        print("   ✅ Solana数据服务初始化成功")
        print(f"      是否有RPC客户端: {service.rpc_client is not None}")
        print(f"      是否有Solscan客户端: {service.solscan_client is not None}")
        print(f"      是否有Helius客户端: {service.helius_client is not None}")
    except Exception as e:
        print(f"   ❌ Solana数据服务初始化失败: {str(e)}")

def test_mock_data_generation():
    """测试模拟数据生成"""
    print("\n🧪 测试模拟数据生成...")
    
    try:
        from src.crypto_trading_agents.services.onchain_data.solana_data_service import SolanaDataService
        # 创建一个简单的配置
        config = {
            "apis": {
                "data": {
                    "onchain_data": {
                        "solana": {
                            "enabled": True,
                            "rpc": {
                                "enabled": False,  # 禁用实际客户端以测试模拟数据
                                "url": None
                            },
                            "solscan": {
                                "enabled": False,
                                "api_key": None
                            },
                            "helius": {
                                "enabled": False,
                                "api_key": None
                            }
                        }
                    }
                }
            }
        }
        
        service = SolanaDataService(config)
        
        # 测试网络健康度数据生成
        network_health = service.get_network_health("SOL", 30)
        print("   ✅ 网络健康度模拟数据生成成功")
        print(f"      数据来源: {network_health.get('source')}")
        print(f"      TPS: {network_health.get('tps')}")
        print(f"      活跃验证者: {network_health.get('active_validators')}")
        
        # 测试活跃账户数据生成
        active_accounts = service.get_active_accounts("SOL", 30)
        print("   ✅ 活跃账户模拟数据生成成功")
        print(f"      数据来源: {active_accounts.get('source')}")
        print(f"      日活跃账户: {active_accounts.get('daily_active')}")
        
        # 测试交易指标数据生成
        tx_metrics = service.get_transaction_metrics("SOL", 30)
        print("   ✅ 交易指标模拟数据生成成功")
        print(f"      数据来源: {tx_metrics.get('source')}")
        print(f"      日交易量: {tx_metrics.get('daily_transactions')}")
        print(f"      平均手续费: {tx_metrics.get('average_fee')}")
        
        # 测试质押指标数据生成
        staking_metrics = service.get_staking_metrics("SOL")
        print("   ✅ 质押指标模拟数据生成成功")
        print(f"      数据来源: {staking_metrics.get('source')}")
        print(f"      总质押量: {staking_metrics.get('total_staked')}")
        
        # 测试DeFi指标数据生成
        defi_metrics = service.get_defi_metrics("SOL", 30)
        print("   ✅ DeFi指标模拟数据生成成功")
        print(f"      数据来源: {defi_metrics.get('source')}")
        print(f"      TVL: {defi_metrics.get('total_value_locked')}")
        
    except Exception as e:
        print(f"   ❌ 模拟数据生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_solana_integration_with_unified_service():
    """测试Solana与统一链上数据服务的集成"""
    print("\n🧪 测试Solana与统一链上数据服务集成...")
    
    try:
        # 创建配置
        test_config = {
            "apis": {
                "data": {
                    "onchain_data": {
                        "solana": {
                            "enabled": True,
                            "rpc": {
                                "enabled": False,  # 使用模拟数据
                                "url": None
                            },
                            "solscan": {
                                "enabled": False,
                                "api_key": None
                            },
                            "helius": {
                                "enabled": False,
                                "api_key": None
                            }
                        }
                    }
                }
            }
        }
        
        # 初始化统一链上数据服务
        from src.crypto_trading_agents.services.onchain_data.onchain_data_service import OnchainDataService
        unified_service = OnchainDataService(test_config)
        
        # 测试Solana数据获取
        print("\n1. 测试通过统一服务获取Solana活跃地址...")
        try:
            active_addresses = unified_service.get_active_addresses("SOL", "solana", "2025-08-08")
            print(f"   ✅ Solana活跃地址数据获取成功: {active_addresses.get('source', 'unknown')}")
            if 'solana_data' in active_addresses:
                solana_data = active_addresses['solana_data']
                print(f"      日活跃账户: {solana_data.get('daily_active', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Solana活跃地址数据获取失败: {str(e)}")
        
        # 测试Solana网络健康度获取
        print("\n2. 测试通过统一服务获取Solana网络健康度...")
        try:
            network_health = unified_service.get_network_health("SOL", "solana", "2025-08-08")
            print(f"   ✅ Solana网络健康度数据获取成功: {network_health.get('source', 'unknown')}")
            if 'solana_data' in network_health:
                solana_data = network_health['solana_data']
                print(f"      TPS: {solana_data.get('tps', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Solana网络健康度数据获取失败: {str(e)}")
        
        # 测试Solana交易指标获取
        print("\n3. 测试通过统一服务获取Solana交易指标...")
        try:
            tx_metrics = unified_service.get_transaction_metrics("SOL", "solana", "2025-08-08")
            print(f"   ✅ Solana交易指标数据获取成功: {tx_metrics.get('source', 'unknown')}")
            if 'solana_data' in tx_metrics:
                solana_data = tx_metrics['solana_data']
                print(f"      日交易量: {solana_data.get('daily_transactions', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Solana交易指标数据获取失败: {str(e)}")
        
        # 测试传统区块链数据获取(对比测试)
        print("\n4. 测试传统区块链数据获取(BTC)...")
        try:
            btc_active_addresses = unified_service.get_active_addresses("BTC", "bitcoin", "2025-08-08")
            print(f"   ✅ BTC活跃地址数据获取成功: {btc_active_addresses.get('source', 'unknown')}")
            if btc_active_addresses.get('source') == 'mock':
                print(f"      日活跃地址: {btc_active_addresses.get('daily_active', 'N/A')}")
        except Exception as e:
            print(f"   ❌ BTC活跃地址数据获取失败: {str(e)}")
            
    except Exception as e:
        print(f"   ❌ Solana与统一服务集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Solana链数据服务测试")
    print("=" * 50)
    
    test_solana_imports()
    test_solana_client_initialization()
    test_solana_service_initialization()
    test_mock_data_generation()
    test_solana_integration_with_unified_service()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")
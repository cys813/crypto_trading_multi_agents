#!/usr/bin/env python3
"""
DeFi分析师测试脚本
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.crypto_trading_agents.agents.analysts.defi_analyst import DefiAnalyst
from src.crypto_trading_agents.unified_config import get_unified_config

def test_defi_analyst():
    """测试DeFi分析师功能"""
    print("🧪 测试DeFi分析师功能...")
    
    # 获取配置
    config = get_unified_config()
    
    # 初始化DeFi分析师
    analyst = DefiAnalyst(config)
    
    # 测试支持DeFi的资产 (ETH)
    print("\n1. 测试ETH/USDT DeFi分析...")
    try:
        # 收集数据
        data = analyst.collect_data("ETH/USDT", datetime.now().strftime("%Y-%m-%d"))
        print(f"   ✅ ETH数据收集成功")
        print(f"      数据源: {data.get('data_source', 'unknown')}")
        print(f"      支持DeFi: {data.get('is_defi_supported', False)}")
        print(f"      协议数量: {len(data.get('protocol_data', {}))}")
        
        # 分析数据
        analysis = analyst.analyze(data)
        print(f"   ✅ ETH分析完成")
        print(f"      AI增强: {analysis.get('ai_enhanced', False)}")
        print(f"      置信度: {analysis.get('confidence', 0):.2f}")
        print(f"      数据质量: {analysis.get('data_quality', {}).get('quality_score', 0):.2f}")
        
    except Exception as e:
        print(f"   ❌ ETH分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试不支持DeFi的资产 (BTC)
    print("\n2. 测试BTC/USDT DeFi分析...")
    try:
        # 收集数据
        data = analyst.collect_data("BTC/USDT", datetime.now().strftime("%Y-%m-%d"))
        print(f"   ✅ BTC数据收集成功")
        print(f"      数据源: {data.get('data_source', 'unknown')}")
        print(f"      支持DeFi: {data.get('is_defi_supported', False)}")
        print(f"      协议数量: {len(data.get('protocol_data', {}))}")
        
        # 分析数据
        analysis = analyst.analyze(data)
        print(f"   ✅ BTC分析完成")
        print(f"      AI增强: {analysis.get('ai_enhanced', False)}")
        print(f"      置信度: {analysis.get('confidence', 0):.2f}")
        print(f"      数据质量: {analysis.get('data_quality', {}).get('quality_score', 0):.2f}")
        print(f"      数据质量详情: {analysis.get('data_quality', {}).get('content_quality', 'unknown')}")
        
    except Exception as e:
        print(f"   ❌ BTC分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试错误处理
    print("\n3. 测试错误处理...")
    try:
        # 测试无效交易对
        data = analyst.collect_data("INVALID/PAIR", datetime.now().strftime("%Y-%m-%d"))
        if "error" in data:
            print(f"   ✅ 错误处理正常: {data['error']}")
        else:
            print(f"   ⚠️  未检测到预期错误")
            
    except Exception as e:
        print(f"   ✅ 错误处理正常: {str(e)}")

def test_defi_data_service():
    """测试DeFi数据服务"""
    print("\n\n🧪 测试DeFi数据服务...")
    
    # 获取配置
    config = get_unified_config()
    
    # 导入DeFi数据服务
    from src.crypto_trading_agents.services.onchain_data.defi_data_service import DeFiDataService
    
    # 初始化DeFi数据服务
    defi_service = DeFiDataService(config)
    
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
        print(f"   ❌ 协议数据获取失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 DeFi分析师功能测试")
    print("=" * 50)
    
    test_defi_data_service()
    test_defi_analyst()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")
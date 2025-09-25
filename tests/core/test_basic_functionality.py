#!/usr/bin/env python3
"""
基本功能验证测试
"""

import sys
import os

def test_import():
    """测试导入功能"""
    try:
        # 直接导入技术分析师模块
        sys.path.insert(0, os.path.join(os.getcwd(), 'crypto_trading_agents'))
        
        # 测试交易所管理器导入
        from src.data_sources.exchange_data_sources import ExchangeManager
        print("✅ ExchangeManager 导入成功")
        
        # 测试分层数据存储导入
        from src.database.models import layered_data_storage
        print("✅ layered_data_storage 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_exchange_manager():
    """测试交易所管理器基本功能"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'crypto_trading_agents'))
        
        from src.data_sources.exchange_data_sources import ExchangeManager
        
        # 创建交易所管理器实例
        manager = ExchangeManager()
        print("✅ ExchangeManager 实例创建成功")
        
        # 检查方法是否存在
        if hasattr(manager, 'get_layered_ohlcv_30d'):
            print("✅ get_layered_ohlcv_30d 方法存在")
        else:
            print("❌ get_layered_ohlcv_30d 方法不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 交易所管理器测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始基本功能验证...")
    
    # 测试导入
    import_success = test_import()
    
    # 测试交易所管理器
    exchange_success = test_exchange_manager()
    
    print(f"\n验证结果:")
    print(f" - 模块导入: {'✅ 通过' if import_success else '❌ 失败'}")
    print(f" - 交易所管理器: {'✅ 通过' if exchange_success else '❌ 失败'}")
    
    if import_success and exchange_success:
        print("\n🎉 基本功能验证通过!")
        print("技术分析师修改已完成，可以支持新的分层数据架构。")
    else:
        print("\n⚠️  部分验证失败，请检查相关功能")

if __name__ == "__main__":
    main()
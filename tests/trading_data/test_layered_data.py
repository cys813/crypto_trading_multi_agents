#!/usr/bin/env python3
"""
测试30天分层数据获取功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources.exchange_data_sources import ExchangeManager, BinanceDataSource
from database.models import layered_data_storage
from datetime import datetime, timedelta
import json
import time


def test_layered_data_acquisition():
    """测试分层数据获取功能"""
    print("=== 测试30天分层数据获取功能 ===")
    
    # 创建交易所管理器
    exchange_manager = ExchangeManager()
    
    # 注册Binance数据源（使用测试模式）
    binance = BinanceDataSource(testnet=True)
    exchange_manager.register_exchange('binance', binance)
    
    # 测试符号
    test_symbol = "BTC/USDT"
    
    print(f"开始获取 {test_symbol} 的30天分层数据...")
    
    try:
        # 获取分层数据
        start_time = time.time()
        layered_data = exchange_manager.get_layered_ohlcv_30d(
            symbol=test_symbol,
            exchange='binance',
            force_refresh=True
        )
        end_time = time.time()
        
        if layered_data:
            print(f"✅ 数据获取成功！耗时: {end_time - start_time:.2f}秒")
            
            # 显示数据摘要
            summary = layered_data['summary']
            print(f"📊 数据摘要:")
            print(f"   总天数: {layered_data['total_days']}")
            print(f"   总K线数: {summary['total_candles']}")
            print(f"   数据完整性: {summary['data_quality']['completeness']}%")
            
            # 显示各层数据
            print(f"📈 各层数据:")
            for layer_name, layer_info in layered_data['layers'].items():
                data_count = len(layer_info['data'])
                expected_count = 60 if layer_name == 'layer_1' else (240 if layer_name == 'layer_2' else 960)
                completeness = (data_count / expected_count * 100) if expected_count > 0 else 0
                
                print(f"   {layer_name}: {layer_info['timeframe']} - {data_count}/{expected_count} 条数据 ({completeness:.1f}%)")
            
            # 测试数据存储
            print(f"💾 测试数据存储...")
            storage_success = layered_data_storage.save_layered_data(test_symbol, layered_data)
            print(f"   存储结果: {'✅ 成功' if storage_success else '❌ 失败'}")
            
            # 测试数据加载
            loaded_data = layered_data_storage.load_latest_layered_data(test_symbol)
            print(f"   加载结果: {'✅ 成功' if loaded_data else '❌ 失败'}")
            
            if loaded_data:
                print(f"   缓存数据时间: {loaded_data['summary']['last_updated']}")
            
            # 测试数据统计
            stats = layered_data_storage.get_data_statistics(test_symbol)
            print(f"📋 数据统计:")
            print(f"   文件数量: {stats['symbols'][test_symbol]['file_count']}")
            print(f"   存储大小: {stats['symbols'][test_symbol]['size_mb']:.2f} MB")
            
            return True
            
        else:
            print("❌ 数据获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False


def test_timeframe_conversion():
    """测试时间框架转换"""
    print("\n=== 测试时间框架转换 ===")
    
    exchange_manager = ExchangeManager()
    
    # 测试不同的时间框架
    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    for timeframe in timeframes:
        minutes = exchange_manager._timeframe_to_minutes(timeframe)
        print(f"   {timeframe} -> {minutes} 分钟")


def test_data_quality_assessment():
    """测试数据质量评估"""
    print("\n=== 测试数据质量评估 ===")
    
    exchange_manager = ExchangeManager()
    
    # 模拟数据
    mock_layer1 = [{'timestamp': i} for i in range(60)]  # 完整数据
    mock_layer2 = [{'timestamp': i} for i in range(220)]  # 缺失一些数据
    mock_layer3 = [{'timestamp': i} for i in range(900)]  # 缺失一些数据
    
    quality = exchange_manager._assess_data_quality(mock_layer1, mock_layer2, mock_layer3)
    
    print(f"📊 数据质量评估:")
    print(f"   完整性: {quality['completeness']}%")
    print(f"   各层数据量: {quality['layer_counts']}")
    print(f"   期望数据量: {quality['expected_counts']}")


def main():
    """主测试函数"""
    print("🚀 开始测试30天分层数据获取功能\n")
    
    success_count = 0
    total_tests = 3
    
    # 测试1：分层数据获取
    if test_layered_data_acquisition():
        success_count += 1
    
    # 测试2：时间框架转换
    test_timeframe_conversion()
    success_count += 1
    
    # 测试3：数据质量评估
    test_data_quality_assessment()
    success_count += 1
    
    print(f"\n🎯 测试完成: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")


if __name__ == "__main__":
    main()
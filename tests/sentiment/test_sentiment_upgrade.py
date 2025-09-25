#!/usr/bin/env python3
"""
情绪分析师升级测试脚本
用于验证新的API集成功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crypto_trading_agents.agents.analysts.sentiment_analyst import SentimentAnalyst
from crypto_trading_agents.default_config import get_config
import json
from datetime import datetime

def main():
    """主测试函数"""
    print("=" * 60)
    print("情绪分析师API集成升级测试")
    print("=" * 60)
    
    # 初始化配置
    config = get_config()
    
    # 创建情绪分析师实例
    analyst = SentimentAnalyst(config)
    
    # 运行测试
    test_results = analyst.test_api_methods("BTC", "2025-01-01")
    
    # 输出详细结果
    print("\n" + "=" * 60)
    print("测试结果详情")
    print("=" * 60)
    
    for method_name, result in test_results.items():
        if method_name == 'summary':
            continue
            
        print(f"\n{method_name.upper()} 方法测试:")
        print(f"  状态: {'✅ 成功' if result.get('success') else '❌ 失败'}")
        
        if result.get('success'):
            print(f"  数据格式: {'✅ 有效' if result.get('valid') else '❌ 无效'}")
            if result.get('missing_keys'):
                print(f"  缺失字段: {result['missing_keys']}")
            
            # 显示部分数据样本
            data = result.get('data', {})
            print(f"  数据样本:")
            for key, value in list(data.items())[:3]:
                if isinstance(value, list):
                    print(f"    {key}: {value[:3]}..." if len(value) > 3 else f"    {key}: {value}")
                else:
                    print(f"    {key}: {value}")
        else:
            print(f"  错误: {result.get('error', '未知错误')}")
    
    # 输出汇总
    summary = test_results.get('summary', {})
    print(f"\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    print(f"总方法数: {summary.get('total_methods', 0)}")
    print(f"成功方法数: {summary.get('successful_methods', 0)}")
    print(f"成功率: {summary.get('success_rate', 0):.1%}")
    print(f"整体状态: {'✅ 全部成功' if summary.get('all_methods_working') else '⚠️ 部分失败'}")
    
    # 测试完整的数据收集流程
    print(f"\n" + "=" * 60)
    print("测试完整数据收集流程")
    print("=" * 60)
    
    try:
        print("运行 collect_data 方法...")
        data = analyst.collect_data("BTC", "2025-01-01")
        
        print("✅ collect_data 执行成功!")
        print("收集到的数据源:")
        for key in data.keys():
            if isinstance(data[key], dict):
                print(f"  - {key}: {len(data[key])} 个字段")
            else:
                print(f"  - {key}: {type(data[key])}")
        
        # 测试传统分析
        print("\n运行传统分析...")
        traditional_result = analyst._traditional_analyze(data)
        print("✅ 传统分析执行成功!")
        print(f"整体情绪: {traditional_result.get('overall_sentiment', 'N/A')}")
        print(f"置信度: {traditional_result.get('confidence', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 完整流程测试失败: {str(e)}")
    
    print(f"\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
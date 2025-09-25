#!/usr/bin/env python3
"""
多源聚合系统综合测试
测试所有数据源的多源聚合功能，包括Twitter、Reddit、新闻、Telegram和YouTube
"""
import sys
import os
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crypto_trading_agents.default_config import DEFAULT_CONFIG
from crypto_trading_agents.agents.analysts.sentiment_analyst import SentimentAnalyst

def test_individual_data_sources():
    """测试各个数据源管理器"""
    print("=== 各数据源管理器独立测试 ===\n")
    
    analyst = SentimentAnalyst(DEFAULT_CONFIG)
    currency = "BTC"
    end_date = "2025-01-15"
    
    data_sources = [
        ("Twitter", "_twitter_manager", analyst._collect_twitter_sentiment),
        ("Reddit", "_reddit_manager", analyst._collect_reddit_sentiment),
        ("新闻", "_news_manager", analyst._collect_news_sentiment),
        ("Telegram", "_telegram_manager", analyst._collect_telegram_sentiment),
        ("YouTube", "_youtube_manager", analyst._collect_influencer_opinions)
    ]
    
    results = {}
    
    for name, manager_attr, collect_method in data_sources:
        print(f"测试 {name} 数据源...")
        
        try:
            start_time = time.time()
            data = collect_method(currency, end_date)
            elapsed_time = time.time() - start_time
            
            # 检查管理器是否已创建
            if hasattr(analyst, manager_attr):
                manager = getattr(analyst, manager_attr)
                status = manager.get_source_status()
                
                print(f"  ✅ 成功获取数据 (耗时: {elapsed_time:.2f}秒)")
                print(f"  数据源: {data.get('_source', 'unknown')}")
                print(f"  数据键数量: {len(data)} 个")
                
                print(f"  数据源状态:")
                for source_type, info in status.items():
                    available = "✅" if info['available'] else "❌"
                    success_rate = info['success_rate']
                    should_skip = "⚠️" if info['should_skip'] else "✅"
                    print(f"    {source_type}: 可用={available}, 成功率={success_rate:.2f}, 跳过={should_skip}")
                
                results[name] = {
                    'success': True,
                    'data': data,
                    'status': status,
                    'response_time': elapsed_time
                }
            else:
                print(f"  ⚠️ 管理器未初始化")
                results[name] = {'success': False, 'error': 'Manager not initialized'}
                
        except Exception as e:
            print(f"  ❌ 测试失败: {str(e)}")
            results[name] = {'success': False, 'error': str(e)}
        
        print()
    
    return results

def test_sentiment_analyst_integration():
    """测试SentimentAnalyst完整集成"""
    print("=== SentimentAnalyst 完整集成测试 ===\n")
    
    analyst = SentimentAnalyst(DEFAULT_CONFIG)
    currency = "BTC"
    end_date = "2025-01-15"
    
    print(f"测试参数:")
    print(f"  货币: {currency}")
    print(f"  结束日期: {end_date}")
    print()
    
    try:
        print("执行完整情绪分析...")
        start_time = time.time()
        
        # 执行完整分析
        result = analyst.analyze_sentiment(currency, end_date)
        
        elapsed_time = time.time() - start_time
        
        print(f"✅ 完整分析成功 (耗时: {elapsed_time:.2f}秒)")
        
        # 显示分析结果摘要
        if result:
            print(f"\n分析结果摘要:")
            overall_sentiment = result.get('overall_sentiment', {})
            print(f"  总体情绪: {overall_sentiment.get('sentiment', 'unknown')}")
            print(f"  置信度: {overall_sentiment.get('confidence', 0):.2f}")
            print(f"  强度: {overall_sentiment.get('intensity', 'unknown')}")
            
            # 各数据源情绪
            individual_analysis = result.get('individual_analysis', {})
            print(f"\n各数据源情绪:")
            for source, analysis in individual_analysis.items():
                if isinstance(analysis, dict):
                    sentiment = analysis.get('sentiment', 'unknown')
                    intensity = analysis.get('intensity', 'unknown')
                    print(f"  {source}: {sentiment} ({intensity})")
            
            # 关键信号
            key_signals = result.get('key_sentiment_signals', [])
            if key_signals:
                print(f"\n关键信号:")
                for signal in key_signals[:5]:
                    print(f"  - {signal}")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_functionality():
    """测试缓存功能"""
    print("\n=== 缓存功能测试 ===\n")
    
    analyst = SentimentAnalyst(DEFAULT_CONFIG)
    currency = "ETH"
    end_date = "2025-01-15"
    
    print("第一次获取数据（应该从实际源获取）...")
    start_time1 = time.time()
    data1 = analyst._collect_twitter_sentiment(currency, end_date)
    elapsed_time1 = time.time() - start_time1
    
    print(f"第一次耗时: {elapsed_time1:.3f}秒")
    print(f"数据源: {data1.get('_source', 'unknown')}")
    
    print("\n第二次获取数据（应该使用缓存）...")
    start_time2 = time.time()
    data2 = analyst._collect_twitter_sentiment(currency, end_date)
    elapsed_time2 = time.time() - start_time2
    
    print(f"第二次耗时: {elapsed_time2:.3f}秒")
    print(f"数据源: {data2.get('_source', 'unknown')}")
    
    if data2.get('_source') == 'cache':
        print("✅ 缓存工作正常")
        speedup = elapsed_time1 / max(elapsed_time2, 0.001)
        print(f"加速比: {speedup:.1f}x")
    else:
        print("⚠️ 缓存可能未工作")
    
    return data2.get('_source') == 'cache'

def test_source_status_monitoring():
    """测试数据源状态监控"""
    print("\n=== 数据源状态监控测试 ===\n")
    
    analyst = SentimentAnalyst(DEFAULT_CONFIG)
    
    # 先执行一些操作来初始化管理器
    analyst._collect_twitter_sentiment("BTC", "2025-01-15")
    analyst._collect_reddit_sentiment("BTC", "2025-01-15")
    analyst._collect_news_sentiment("BTC", "2025-01-15")
    
    print("获取所有数据源状态...")
    try:
        all_status = analyst.get_all_data_source_status()
        
        print("数据源状态监控:")
        for platform, sources in all_status.items():
            print(f"\n{platform.upper()} 数据源:")
            for source_type, info in sources.items():
                available = "✅" if info['available'] else "❌"
                success_rate = info['success_rate']
                should_skip = "⚠️" if info['should_skip'] else "✅"
                print(f"  {source_type}:")
                print(f"    可用性: {available}")
                print(f"    成功率: {success_rate:.2f}")
                print(f"    跳过状态: {should_skip}")
        
        return True
        
    except Exception as e:
        print(f"❌ 状态监控测试失败: {str(e)}")
        return False

def test_cache_cleanup():
    """测试缓存清理功能"""
    print("\n=== 缓存清理测试 ===\n")
    
    analyst = SentimentAnalyst(DEFAULT_CONFIG)
    
    # 先执行一些操作来填充缓存
    analyst._collect_twitter_sentiment("BTC", "2025-01-15")
    analyst._collect_reddit_sentiment("ETH", "2025-01-15")
    
    try:
        print("清理所有缓存...")
        cleared_counts = analyst.clear_all_caches()
        
        print("清理结果:")
        total_cleared = 0
        for platform, count in cleared_counts.items():
            print(f"  {platform}: 清理了 {count} 个缓存条目")
            total_cleared += count
        
        print(f"总计清理: {total_cleared} 个缓存条目")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存清理测试失败: {str(e)}")
        return False

def run_comprehensive_test():
    """运行综合测试"""
    print("多源聚合系统综合测试")
    print("=" * 60)
    print()
    
    test_results = {}
    
    # 测试1: 各数据源独立测试
    try:
        test_results['individual_sources'] = test_individual_data_sources()
    except Exception as e:
        print(f"独立数据源测试出错: {e}")
        test_results['individual_sources'] = {'error': str(e)}
    
    print("\n" + "=" * 60 + "\n")
    
    # 测试2: 完整集成测试
    try:
        test_results['integration'] = test_sentiment_analyst_integration()
    except Exception as e:
        print(f"集成测试出错: {e}")
        test_results['integration'] = {'error': str(e)}
    
    # 测试3: 缓存功能测试
    try:
        test_results['cache'] = test_cache_functionality()
    except Exception as e:
        print(f"缓存测试出错: {e}")
        test_results['cache'] = {'error': str(e)}
    
    # 测试4: 状态监控测试
    try:
        test_results['monitoring'] = test_source_status_monitoring()
    except Exception as e:
        print(f"监控测试出错: {e}")
        test_results['monitoring'] = {'error': str(e)}
    
    # 测试5: 缓存清理测试
    try:
        test_results['cleanup'] = test_cache_cleanup()
    except Exception as e:
        print(f"清理测试出错: {e}")
        test_results['cleanup'] = {'error': str(e)}
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    for test_name, result in test_results.items():
        if test_name == 'individual_sources':
            # 统计各数据源测试结果
            for source_name, source_result in result.items():
                if isinstance(source_result, dict):
                    total_tests += 1
                    if source_result.get('success', False):
                        success_count += 1
                        print(f"✅ {source_name} 数据源测试: 通过")
                    else:
                        error = source_result.get('error', 'Unknown error')
                        print(f"❌ {source_name} 数据源测试: 失败 ({error})")
        else:
            total_tests += 1
            if result == True or (isinstance(result, dict) and result.get('success', False)):
                success_count += 1
                print(f"✅ {test_name.replace('_', ' ').title()}: 通过")
            else:
                if isinstance(result, dict) and 'error' in result:
                    error = result['error']
                else:
                    error = str(result)
                print(f"❌ {test_name.replace('_', ' ').title()}: 失败 ({error})")
    
    print(f"\n总体结果: {success_count}/{total_tests} 测试通过")
    
    if success_count == total_tests:
        print("🎉 所有测试都通过了！多源聚合系统运行正常。")
    elif success_count > total_tests * 0.7:
        print("⚠️ 大部分测试通过，系统基本可用，建议检查失败的组件。")
    else:
        print("🚨 多个测试失败，建议检查系统配置和依赖。")
    
    return test_results

def main():
    """主函数"""
    try:
        results = run_comprehensive_test()
        
        # 保存测试结果
        try:
            import json
            with open('test_results.json', 'w', encoding='utf-8') as f:
                # 转换结果为JSON可序列化格式
                json_results = {}
                for key, value in results.items():
                    if isinstance(value, dict):
                        json_results[key] = {}
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, dict):
                                # 过滤掉不能序列化的数据
                                json_sub_value = {}
                                for k, v in sub_value.items():
                                    if k not in ['data', 'status']:  # 跳过复杂的数据结构
                                        json_sub_value[k] = v
                                json_results[key][sub_key] = json_sub_value
                            else:
                                json_results[key][sub_key] = sub_value
                    else:
                        json_results[key] = value
                
                json.dump(json_results, f, indent=2, ensure_ascii=False)
            print(f"\n测试结果已保存到 test_results.json")
        except Exception as e:
            print(f"保存测试结果时出错: {e}")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
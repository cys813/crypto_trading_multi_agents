"""
新的K线数据系统使用示例

演示如何使用新的多时间周期K线数据结构和分析方法
"""

from src.crypto_trading_agents.services.kline_data_service import KlineDataService
from src.crypto_trading_agents.agents.researchers.bull_researcher import BullResearcher
from src.crypto_trading_agents.agents.researchers.bear_researcher import BearResearcher
from datetime import datetime
import json

def example_new_kline_system():
    """演示新的K线数据系统"""
    
    # 配置
    config = {
        "kline_data_config": {
            "data_source": "mock",  # 使用模拟数据
            "cache_expiry": 300
        },
        "llm_service_config": {
            "provider": "openai",
            "model": "gpt-4"
        }
    }
    
    # 初始化服务
    kline_service = KlineDataService(config)
    bull_researcher = BullResearcher(config)
    bear_researcher = BearResearcher(config)
    
    # 测试交易对
    symbol = "BTC/USDT"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"=== 新K线数据系统演示 ===")
    print(f"交易对: {symbol}")
    print(f"截止日期: {end_date}")
    print()
    
    # 1. 测试K线数据服务
    print("1. 测试K线数据服务")
    print("-" * 30)
    
    # 收集多时间周期数据
    kline_data = kline_service.collect_multi_timeframe_kline_data(symbol, end_date)
    
    if "error" not in kline_data:
        print(f"✓ 成功收集多时间周期数据")
        print(f"  数据类型: {kline_data['data_type']}")
        print(f"  可用时间周期: {list(kline_data['timeframes'].keys())}")
        
        # 显示各时间周期数据统计
        for timeframe, tf_data in kline_data['timeframes'].items():
            print(f"  {timeframe}: {tf_data['data_count']} 条数据")
        
        # 显示数据质量
        quality = kline_data.get('data_quality', {})
        print(f"  数据质量: {quality.get('overall_quality', 0):.2f} ({quality.get('quality_level', 'unknown')})")
        
    else:
        print(f"✗ K线数据收集失败: {kline_data['error']}")
        return
    
    print()
    
    # 2. 测试牛市研究员
    print("2. 测试牛市研究员")
    print("-" * 30)
    
    bull_data = bull_researcher.collect_data(symbol, end_date)
    
    if "error" not in bull_data:
        print(f"✓ 牛市研究数据收集成功")
        print(f"  数据类型: {bull_data['data_type']}")
        
        if "timeframe_signals" in bull_data:
            print(f"  时间周期信号:")
            for timeframe, signals in bull_data["timeframe_signals"].items():
                score = signals.get("timeframe_bull_score", 0)
                print(f"    {timeframe}: {score:.3f}")
        
        if "cross_timeframe_signals" in bull_data:
            cross_signals = bull_data["cross_timeframe_signals"]
            print(f"  跨时间周期强度: {cross_signals.get('cross_timeframe_strength', 0):.3f}")
            print(f"  信号一致性: {cross_signals.get('consensus', 'unknown')}")
        
        print(f"  整体牛市评分: {bull_data.get('overall_bull_score', 0):.3f}")
        
        # 显示关键指标
        key_indicators = bull_data.get('key_bull_indicators', [])
        if key_indicators:
            print(f"  关键牛市指标: {', '.join(key_indicators[:3])}")
        
    else:
        print(f"✗ 牛市研究数据收集失败: {bull_data['error']}")
    
    print()
    
    # 3. 测试熊市研究员
    print("3. 测试熊市研究员")
    print("-" * 30)
    
    bear_data = bear_researcher.collect_data(symbol, end_date)
    
    if "error" not in bear_data:
        print(f"✓ 熊市研究数据收集成功")
        print(f"  数据类型: {bear_data['data_type']}")
        
        if "timeframe_signals" in bear_data:
            print(f"  时间周期信号:")
            for timeframe, signals in bear_data["timeframe_signals"].items():
                score = signals.get("timeframe_bear_score", 0)
                print(f"    {timeframe}: {score:.3f}")
        
        if "cross_timeframe_signals" in bear_data:
            cross_signals = bear_data["cross_timeframe_signals"]
            print(f"  跨时间周期强度: {cross_signals.get('cross_timeframe_strength', 0):.3f}")
            print(f"  信号一致性: {cross_signals.get('consensus', 'unknown')}")
        
        print(f"  整体熊市评分: {bear_data.get('overall_bear_score', 0):.3f}")
        
        # 显示关键指标
        key_indicators = bear_data.get('key_bear_indicators', [])
        if key_indicators:
            print(f"  关键熊市指标: {', '.join(key_indicators[:3])}")
        
    else:
        print(f"✗ 熊市研究数据收集失败: {bear_data['error']}")
    
    print()
    
    # 4. 演示数据摘要
    print("4. 数据摘要对比")
    print("-" * 30)
    
    # 获取K线数据摘要
    summary = kline_service.get_latest_kline_summary(symbol)
    
    if "error" not in summary:
        print(f"✓ K线数据摘要:")
        print(f"  可用时间周期: {summary.get('available_timeframes', [])}")
        
        latest_prices = summary.get('latest_prices', {})
        if latest_prices:
            print(f"  最新价格:")
            for timeframe, price_data in latest_prices.items():
                print(f"    {timeframe}: {price_data['close']:.2f}")
    
    print()
    
    # 5. 系统特性总结
    print("5. 新系统特性总结")
    print("-" * 30)
    print("✓ 多时间周期K线数据支持 (4h, 3h, 1h)")
    print("✓ 统一的数据服务接口")
    print("✓ 智能数据质量评估")
    print("✓ 跨时间周期信号分析")
    print("✓ 原始K线数据传递给AI模型")
    print("✓ 向后兼容现有数据格式")
    print("✓ 可配置的数据源 (mock/binance/其他)")
    print("✓ 数据缓存机制")
    print("✓ 统计信息自动计算")
    
    print()
    print("=== 演示完成 ===")

def example_data_structure():
    """演示新的数据结构"""
    
    print("=== 新K线数据结构示例 ===")
    print()
    
    # 示例多时间周期数据结构
    example_structure = {
        "symbol": "BTC/USDT",
        "end_date": "2024-01-15",
        "data_type": "multi_timeframe",
        "timeframes": {
            "4h": {
                "symbol": "BTC/USDT",
                "timeframe": "4h",
                "data": [
                    [1642243200000, 47000.0, 47500.0, 46800.0, 47200.0, 1250000000],
                    [1642246800000, 47200.0, 47800.0, 47100.0, 47600.0, 1300000000],
                    # ... 更多数据
                ],
                "data_count": 30,
                "source": "mock"
            },
            "3h": {
                "symbol": "BTC/USDT", 
                "timeframe": "3h",
                "data": [
                    [1642243200000, 47000.0, 47500.0, 46800.0, 47200.0, 1250000000],
                    [1642245000000, 47200.0, 47800.0, 47100.0, 47600.0, 1300000000],
                    # ... 更多数据
                ],
                "data_count": 24,
                "source": "mock"
            },
            "1h": {
                "symbol": "BTC/USDT",
                "timeframe": "1h", 
                "data": [
                    [1642243200000, 47000.0, 47500.0, 46800.0, 47200.0, 1250000000],
                    [1642246800000, 47200.0, 47800.0, 47100.0, 47600.0, 1300000000],
                    # ... 更多数据
                ],
                "data_count": 360,
                "source": "mock"
            }
        },
        "statistics": {
            "timeframes": {
                "4h": {
                    "price_change": 0.025,
                    "volatility": 0.035,
                    "avg_volume": 1280000000
                },
                "3h": {
                    "price_change": 0.022,
                    "volatility": 0.032,
                    "avg_volume": 1150000000
                },
                "1h": {
                    "price_change": 0.018,
                    "volatility": 0.028,
                    "avg_volume": 980000000
                }
            },
            "overall": {
                "total_price_change": 0.022,
                "overall_volatility": 0.032,
                "total_data_points": 414
            }
        },
        "data_quality": {
            "overall_quality": 0.92,
            "quality_level": "excellent",
            "timeframe_scores": {
                "4h": 0.95,
                "3h": 0.90,
                "1h": 0.91
            }
        }
    }
    
    print("多时间周期K线数据结构:")
    print(json.dumps(example_structure, indent=2, ensure_ascii=False))
    
    print()
    print("主要改进:")
    print("1. 统一的时间周期数据格式")
    print("2. 内置数据质量评估")
    print("3. 详细的统计信息")
    print("4. 支持多种数据源")
    print("5. 标准化的OHLCV数据结构")

if __name__ == "__main__":
    example_new_kline_system()
    print()
    example_data_structure()
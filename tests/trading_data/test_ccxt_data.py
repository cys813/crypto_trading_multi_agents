"""
测试CCXT数据获取功能

验证通过CCXT获取真实交易数据的功能
"""

import os
import sys
import time
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../crypto_trading_agents'))

from utils.exchange_setup import initialize_exchanges, exchange_setup, exchange_manager


def test_ticker_data():
    """测试行情数据获取"""
    print("\n=== 测试行情数据获取 ===")
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    for symbol in symbols:
        print(f"\n获取 {symbol} 行情数据...")
        
        # 尝试从不同交易所获取
        exchanges = ['binance', 'okx', 'huobi']
        
        for exchange_name in exchanges:
            try:
                ticker = exchange_manager.get_ticker(symbol, exchange_name)
                if ticker:
                    print(f"  ✓ {exchange_name}:")
                    print(f"    价格: {ticker['price']}")
                    print(f"    24h最高: {ticker['high']}")
                    print(f"    24h最低: {ticker['low']}")
                    print(f"    24h成交量: {ticker['volume']}")
                    break
            except Exception as e:
                print(f"  ✗ {exchange_name}: {e}")
        
        # 获取聚合价格
        try:
            aggregated = exchange_manager.get_aggregated_price(symbol)
            if aggregated:
                print(f"  📊 聚合价格:")
                print(f"    加权平均价: {aggregated['weighted_price']}")
                print(f"    总成交量: {aggregated['total_volume']}")
                print(f"    交易所数量: {aggregated['exchange_count']}")
        except Exception as e:
            print(f"  ✗ 聚合价格获取失败: {e}")


def test_ohlcv_data():
    """测试K线数据获取"""
    print("\n=== 测试K线数据获取 ===")
    
    symbol = 'BTC/USDT'
    timeframes = ['1h', '4h', '1d']
    
    for timeframe in timeframes:
        print(f"\n获取 {symbol} {timeframe} K线数据...")
        
        try:
            ohlcv = exchange_manager.get_ohlcv(symbol, timeframe, limit=10)
            if ohlcv:
                print(f"  ✓ 成功获取 {len(ohlcv)} 条K线数据")
                
                # 显示最新几条数据
                for i, candle in enumerate(ohlcv[-3:]):
                    print(f"    {i+1}. 时间: {candle['datetime']}")
                    print(f"       开: {candle['open']}, 高: {candle['high']}")
                    print(f"       低: {candle['low']}, 收: {candle['close']}")
                    print(f"       成交量: {candle['volume']}")
            else:
                print(f"  ✗ 获取K线数据失败")
                
        except Exception as e:
            print(f"  ✗ 获取K线数据失败: {e}")


def test_order_book_data():
    """测试订单簿数据获取"""
    print("\n=== 测试订单簿数据获取 ===")
    
    symbol = 'BTC/USDT'
    
    try:
        order_book = exchange_manager.get_order_book(symbol, limit=5)
        if order_book:
            print(f"  ✓ 订单簿数据获取成功")
            print(f"    时间戳: {order_book['timestamp']}")
            
            print(f"    买单 (前5):")
            for i, (price, amount) in enumerate(order_book['bids'][:5]):
                print(f"      {i+1}. 价格: {price}, 数量: {amount}")
            
            print(f"    卖单 (前5):")
            for i, (price, amount) in enumerate(order_book['asks'][:5]):
                print(f"      {i+1}. 价格: {price}, 数量: {amount}")
        else:
            print(f"  ✗ 订单簿数据获取失败")
            
    except Exception as e:
        print(f"  ✗ 订单簿数据获取失败: {e}")


def test_market_depth():
    """测试市场深度分析"""
    print("\n=== 测试市场深度分析 ===")
    
    symbol = 'BTC/USDT'
    
    try:
        depth = exchange_manager.get_market_depth(symbol)
        if depth:
            print(f"  ✓ 市场深度分析成功")
            print(f"    买压: {depth['bid_pressure']}")
            print(f"    卖压: {depth['ask_pressure']}")
            print(f"    压力比: {depth['pressure_ratio']:.2f}")
            print(f"    价差: {depth['spread']}")
            print(f"    价差百分比: {depth['spread_percentage']:.2f}%")
            print(f"    最高买价: {depth['top_bid']}")
            print(f"    最低卖价: {depth['top_ask']}")
        else:
            print(f"  ✗ 市场深度分析失败")
            
    except Exception as e:
        print(f"  ✗ 市场深度分析失败: {e}")


def test_recent_trades():
    """测试最近交易数据获取"""
    print("\n=== 测试最近交易数据获取 ===")
    
    symbol = 'BTC/USDT'
    
    # 直接从交易所实例获取
    exchanges = ['binance', 'okx', 'huobi']
    
    for exchange_name in exchanges:
        try:
            exchange = exchange_manager.get_exchange(exchange_name)
            if exchange:
                trades = exchange.get_recent_trades(symbol, limit=5)
                if trades:
                    print(f"  ✓ {exchange_name} 最近交易:")
                    for i, trade in enumerate(trades[:3]):
                        print(f"    {i+1}. 时间: {trade['datetime']}")
                        print(f"       价格: {trade['price']}")
                        print(f"       数量: {trade['amount']}")
                        print(f"       方向: {trade['side']}")
                    break
        except Exception as e:
            print(f"  ✗ {exchange_name} 交易数据获取失败: {e}")


def test_caching_performance():
    """测试缓存性能"""
    print("\n=== 测试缓存性能 ===")
    
    symbol = 'BTC/USDT'
    
    # 第一次获取（无缓存）
    start_time = time.time()
    ticker1 = exchange_manager.get_ticker(symbol)
    first_time = time.time() - start_time
    
    # 第二次获取（有缓存）
    start_time = time.time()
    ticker2 = exchange_manager.get_ticker(symbol)
    second_time = time.time() - start_time
    
    print(f"  第一次获取时间: {first_time:.3f} 秒")
    print(f"  第二次获取时间: {second_time:.3f} 秒")
    print(f"  缓存加速: {first_time/second_time:.1f}x" if second_time > 0 else "  缓存加速: 无限大")


def test_technical_analyst_integration():
    """测试技术分析师集成"""
    print("\n=== 测试技术分析师集成 ===")
    
    try:
        from agents.analysts.technical_analyst import TechnicalAnalyst
        
        # 创建技术分析师实例
        config = {
            'analysis_config': {
                'technical_indicators': ['rsi', 'macd', 'bollinger_bands']
            }
        }
        analyst = TechnicalAnalyst(config)
        
        # 测试数据收集
        symbol = 'BTC/USDT'
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"  收集 {symbol} 技术分析数据...")
        data = analyst.collect_data(symbol, end_date)
        
        if 'error' not in data:
            print(f"  ✓ 数据收集成功")
            print(f"    数据源: {data.get('data_source', 'unknown')}")
            print(f"    时间范围: {data.get('start_date')} 到 {data.get('end_date')}")
            print(f"    OHLCV数据点: {len(data.get('ohlcv_data', []))}")
            print(f"    技术指标: {list(data.get('indicators', {}).keys())}")
            
            # 测试分析功能
            analysis = analyst.analyze(data)
            if 'error' not in analysis:
                print(f"  ✓ 技术分析成功")
                print(f"    趋势强度: {analysis.get('trend_strength', {})}")
                print(f"    市场状态: {analysis.get('market_regime', 'unknown')}")
                print(f"    置信度: {analysis.get('confidence', 0):.2f}")
            else:
                print(f"  ✗ 技术分析失败: {analysis['error']}")
        else:
            print(f"  ✗ 数据收集失败: {data['error']}")
            
    except Exception as e:
        print(f"  ✗ 技术分析师集成测试失败: {e}")


def main():
    """主测试函数"""
    print("开始测试CCXT数据获取功能")
    print("=" * 50)
    
    # 初始化交易所
    print("\n正在初始化交易所...")
    results = initialize_exchanges()
    
    if not results['success']:
        print("❌ 没有成功设置任何交易所，无法进行测试")
        return
    
    # 运行测试
    test_functions = [
        test_ticker_data,
        test_ohlcv_data,
        test_order_book_data,
        test_market_depth,
        test_recent_trades,
        test_caching_performance,
        test_technical_analyst_integration
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ 测试 {test_func.__name__} 失败: {e}")
    
    print("\n" + "=" * 50)
    print("CCXT数据获取功能测试完成")
    
    # 显示交易所状态
    print("\n最终交易所状态:")
    status = exchange_setup.get_exchange_status()
    for name, info in status.items():
        status_icon = "✓" if info['status'] == 'active' else "✗"
        print(f"  {status_icon} {name}: {info['status']}")
        if info['exchange_name']:
            print(f"    交易所: {info['exchange_name']}")


if __name__ == "__main__":
    main()
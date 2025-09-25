"""
交易所数据源实现
"""

import ccxt
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
from .crypto_data_sources import BaseDataSource
from enum import Enum
from src.database.models import layered_data_storage


class TimeGranularity(Enum):
    """时间粒度枚举"""
    FOUR_HOUR = "4h"
    ONE_HOUR = "1h"
    FIFTEEN_MIN = "15m"


class DataLayer(Enum):
    """数据分层枚举"""
    LAYER_1 = "layer_1"  # 前10天 - 4小时K线
    LAYER_2 = "layer_2"  # 中间10天 - 1小时K线
    LAYER_3 = "layer_3"  # 最近10天 - 15分钟K线


class ExchangeDataSource(BaseDataSource):
    """交易所数据源基类"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None):
        """
        初始化交易所数据源
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码短语
        """
        super().__init__(api_key)
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.exchange = None
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms请求间隔
    
    def _respect_rate_limit(self):
        """遵守速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        
        self.last_request_time = time.time()
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取行情数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            行情数据
        """
        if not self.exchange:
            return None
        
        try:
            self._respect_rate_limit()
            ticker = self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['quoteVolume'],
                'timestamp': ticker['timestamp'],
                'datetime': ticker['datetime']
            }
        except Exception as e:
            print(f"获取行情数据失败: {e}")
            return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            limit: 限制数量
            
        Returns:
            K线数据列表
        """
        if not self.exchange:
            return None
        
        try:
            self._respect_rate_limit()
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            return [
                {
                    'timestamp': item[0],
                    'datetime': datetime.fromtimestamp(item[0] / 1000).isoformat(),
                    'open': item[1],
                    'high': item[2],
                    'low': item[3],
                    'close': item[4],
                    'volume': item[5]
                }
                for item in ohlcv
            ]
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return None
    
    def get_order_book(self, symbol: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对符号
            limit: 限制数量
            
        Returns:
            订单簿数据
        """
        if not self.exchange:
            return None
        
        try:
            self._respect_rate_limit()
            order_book = self.exchange.fetch_order_book(symbol, limit)
            
            return {
                'symbol': symbol,
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'timestamp': order_book['timestamp'],
                'datetime': order_book['datetime']
            }
        except Exception as e:
            print(f"获取订单簿数据失败: {e}")
            return None
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """
        获取最近交易数据
        
        Args:
            symbol: 交易对符号
            limit: 限制数量
            
        Returns:
            交易数据列表
        """
        if not self.exchange:
            return None
        
        try:
            self._respect_rate_limit()
            trades = self.exchange.fetch_trades(symbol, limit)
            
            return [
                {
                    'timestamp': trade['timestamp'],
                    'datetime': trade['datetime'],
                    'price': trade['price'],
                    'amount': trade['amount'],
                    'side': trade['side']
                }
                for trade in trades
            ]
        except Exception as e:
            print(f"获取交易数据失败: {e}")
            return None


class BinanceDataSource(ExchangeDataSource):
    """Binance交易所数据源"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        """
        初始化Binance数据源
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
        """
        super().__init__(api_key, api_secret)
        
        if testnet:
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'testnet': True,
                'enableRateLimit': True
            })
        else:
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True
            })
        
        self.rate_limit_delay = 0.05  # Binance限制更严格


class CoinbaseDataSource(ExchangeDataSource):
    """Coinbase交易所数据源"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None):
        """
        初始化Coinbase数据源
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码短语
        """
        super().__init__(api_key, api_secret, passphrase)
        
        self.exchange = ccxt.coinbase({
            'apiKey': api_key,
            'secret': api_secret,
            'passphrase': passphrase,
            'enableRateLimit': True
        })
        
        self.rate_limit_delay = 0.1


class OKXDataSource(ExchangeDataSource):
    """OKX交易所数据源"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None):
        """
        初始化OKX数据源
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码短语
        """
        super().__init__(api_key, api_secret, passphrase)
        
        self.exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': api_secret,
            'passphrase': passphrase,
            'enableRateLimit': True
        })
        
        self.rate_limit_delay = 0.05


class HuobiDataSource(ExchangeDataSource):
    """Huobi交易所数据源"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        初始化Huobi数据源
        
        Args:
            api_key: API密钥
            api_secret: API密钥
        """
        super().__init__(api_key, api_secret)
        
        self.exchange = ccxt.huobi({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        
        self.rate_limit_delay = 0.1


class ExchangeManager:
    """交易所管理器"""
    
    def __init__(self):
        """初始化交易所管理器"""
        self.exchanges = {}
        self.cache = {}
        self.cache_ttl = 60  # 1分钟缓存
    
    def register_exchange(self, name: str, exchange: ExchangeDataSource):
        """
        注册交易所
        
        Args:
            name: 交易所名称
            exchange: 交易所数据源实例
        """
        self.exchanges[name] = exchange
    
    def get_exchange(self, name: str) -> Optional[ExchangeDataSource]:
        """
        获取交易所
        
        Args:
            name: 交易所名称
            
        Returns:
            交易所数据源实例或None
        """
        return self.exchanges.get(name)
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存数据或None
        """
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[cache_key]
        return None
    
    def cache_data(self, cache_key: str, data: Dict[str, Any]):
        """
        缓存数据
        
        Args:
            cache_key: 缓存键
            data: 数据
        """
        self.cache[cache_key] = (data, time.time())
    
    def get_ticker(self, symbol: str, exchange: str = 'binance') -> Optional[Dict[str, Any]]:
        """
        获取行情数据
        
        Args:
            symbol: 交易对符号
            exchange: 交易所名称
            
        Returns:
            行情数据
        """
        cache_key = f"ticker_{symbol}_{exchange}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        exchange_obj = self.get_exchange(exchange)
        if exchange_obj:
            data = exchange_obj.get_ticker(symbol)
            if data:
                self.cache_data(cache_key, data)
                return data
        
        return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100, exchange: str = 'binance') -> Optional[List[Dict[str, Any]]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            limit: 限制数量
            exchange: 交易所名称
            
        Returns:
            K线数据列表
        """
        cache_key = f"ohlcv_{symbol}_{timeframe}_{limit}_{exchange}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        exchange_obj = self.get_exchange(exchange)
        if exchange_obj:
            data = exchange_obj.get_ohlcv(symbol, timeframe, limit)
            if data:
                self.cache_data(cache_key, data)
                return data
        
        return None
    
    def get_order_book(self, symbol: str, limit: int = 10, exchange: str = 'binance') -> Optional[Dict[str, Any]]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对符号
            limit: 限制数量
            exchange: 交易所名称
            
        Returns:
            订单簿数据
        """
        cache_key = f"orderbook_{symbol}_{limit}_{exchange}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        exchange_obj = self.get_exchange(exchange)
        if exchange_obj:
            data = exchange_obj.get_order_book(symbol, limit)
            if data:
                self.cache_data(cache_key, data)
                return data
        
        return None
    
    def get_layered_ohlcv_30d(self, symbol: str, exchange: str = 'binance', force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取30天分层K线数据
        
        Args:
            symbol: 交易对符号
            exchange: 交易所名称
            force_refresh: 是否强制刷新数据
            
        Returns:
            分层K线数据
        """
        try:
            # 首先尝试从存储加载
            if not force_refresh:
                cached_data = layered_data_storage.load_latest_layered_data(symbol)
                if cached_data:
                    # 检查数据是否足够新（小于1小时）
                    last_updated = datetime.fromisoformat(cached_data['summary']['last_updated'])
                    if datetime.now() - last_updated < timedelta(hours=1):
                        return cached_data
            
            # 计算时间范围
            end_time = datetime.now()
            
            # 第3层：最近10天 - 15分钟K线
            layer_3_start = end_time - timedelta(days=10)
            layer_3_data = self.get_ohlcv_in_range(
                symbol, TimeGranularity.FIFTEEN_MIN.value, 
                layer_3_start, end_time, exchange
            )
            
            # 第2层：中间10天 - 1小时K线
            layer_2_start = end_time - timedelta(days=20)
            layer_2_end = layer_3_start
            layer_2_data = self.get_ohlcv_in_range(
                symbol, TimeGranularity.ONE_HOUR.value,
                layer_2_start, layer_2_end, exchange
            )
            
            # 第1层：前10天 - 4小时K线
            layer_1_start = end_time - timedelta(days=30)
            layer_1_end = layer_2_start
            layer_1_data = self.get_ohlcv_in_range(
                symbol, TimeGranularity.FOUR_HOUR.value,
                layer_1_start, layer_1_end, exchange
            )
            
            layered_data = {
                'symbol': symbol,
                'exchange': exchange,
                'total_days': 30,
                'layers': {
                    DataLayer.LAYER_1.value: {
                        'timeframe': TimeGranularity.FOUR_HOUR.value,
                        'days': 10,
                        'data': layer_1_data or [],
                        'start_time': layer_1_start.isoformat(),
                        'end_time': layer_1_end.isoformat()
                    },
                    DataLayer.LAYER_2.value: {
                        'timeframe': TimeGranularity.ONE_HOUR.value,
                        'days': 10,
                        'data': layer_2_data or [],
                        'start_time': layer_2_start.isoformat(),
                        'end_time': layer_2_end.isoformat()
                    },
                    DataLayer.LAYER_3.value: {
                        'timeframe': TimeGranularity.FIFTEEN_MIN.value,
                        'days': 10,
                        'data': layer_3_data or [],
                        'start_time': layer_3_start.isoformat(),
                        'end_time': end_time.isoformat()
                    }
                },
                'summary': {
                    'total_candles': len(layer_1_data or []) + len(layer_2_data or []) + len(layer_3_data or []),
                    'data_quality': self._assess_data_quality(layer_1_data, layer_2_data, layer_3_data),
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            # 保存到存储
            layered_data_storage.save_layered_data(symbol, layered_data)
            
            return layered_data
        except Exception as e:
            print(f"获取30天分层K线数据失败: {e}")
            return None
    
    def get_ohlcv_in_range(self, symbol: str, timeframe: str, start_time: datetime, 
                          end_time: datetime, exchange: str = 'binance') -> Optional[List[Dict[str, Any]]]:
        """
        获取指定时间范围内的K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            start_time: 开始时间
            end_time: 结束时间
            exchange: 交易所名称
            
        Returns:
            K线数据列表
        """
        try:
            exchange_obj = self.get_exchange(exchange)
            if not exchange_obj:
                return None
            
            # 计算需要获取的K线数量
            time_diff = end_time - start_time
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            total_candles = int(time_diff.total_seconds() / 60 / timeframe_minutes)
            
            # 添加一些缓冲以获取完整数据
            limit = min(total_candles + 10, 1000)  # CCXT限制
            
            self._respect_rate_limit()
            ohlcv = exchange_obj.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # 过滤时间范围内的数据
            filtered_data = []
            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)
            
            for item in ohlcv:
                if start_timestamp <= item[0] <= end_timestamp:
                    filtered_data.append({
                        'timestamp': item[0],
                        'datetime': datetime.fromtimestamp(item[0] / 1000).isoformat(),
                        'open': item[1],
                        'high': item[2],
                        'low': item[3],
                        'close': item[4],
                        'volume': item[5],
                        'timeframe': timeframe
                    })
            
            return filtered_data
        except Exception as e:
            print(f"获取时间范围K线数据失败: {e}")
            return None
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """将时间框架转换为分钟"""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080
        }
        return timeframe_map.get(timeframe, 60)
    
    def _assess_data_quality(self, layer1_data, layer2_data, layer3_data) -> Dict[str, Any]:
        """评估数据质量"""
        total_expected = 60 + 240 + 960  # 预期总数
        total_actual = len(layer1_data or []) + len(layer2_data or []) + len(layer3_data or [])
        
        completeness = total_actual / total_expected if total_expected > 0 else 0
        
        return {
            'completeness': round(completeness * 100, 2),
            'layer_counts': {
                'layer_1': len(layer1_data or []),
                'layer_2': len(layer2_data or []),
                'layer_3': len(layer3_data or [])
            },
            'expected_counts': {
                'layer_1': 60,
                'layer_2': 240,
                'layer_3': 960
            }
        }
    
    def get_aggregated_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取聚合价格数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            聚合价格数据
        """
        prices = []
        
        for exchange_name, exchange_obj in self.exchanges.items():
            ticker = exchange_obj.get_ticker(symbol)
            if ticker:
                prices.append({
                    'exchange': exchange_name,
                    'price': ticker['price'],
                    'volume': ticker['volume']
                })
        
        if not prices:
            return None
        
        # 计算加权平均价格
        total_volume = sum(p['volume'] for p in prices)
        if total_volume == 0:
            return None
        
        weighted_price = sum(p['price'] * p['volume'] for p in prices) / total_volume
        
        return {
            'symbol': symbol,
            'weighted_price': weighted_price,
            'total_volume': total_volume,
            'exchange_count': len(prices),
            'exchanges': prices,
            'timestamp': int(time.time() * 1000)
        }
    
    def get_market_depth(self, symbol: str, exchange: str = 'binance') -> Optional[Dict[str, Any]]:
        """
        获取市场深度数据
        
        Args:
            symbol: 交易对符号
            exchange: 交易所名称
            
        Returns:
            市场深度数据
        """
        order_book = self.get_order_book(symbol, limit=20, exchange=exchange)
        if not order_book:
            return None
        
        bids = order_book['bids']
        asks = order_book['asks']
        
        # 计算买卖压力
        bid_pressure = sum(bid[1] for bid in bids[:10])
        ask_pressure = sum(ask[1] for ask in asks[:10])
        
        # 计算价差
        if bids and asks:
            spread = asks[0][0] - bids[0][0]
            spread_percentage = (spread / bids[0][0]) * 100
        else:
            spread = 0
            spread_percentage = 0
        
        return {
            'symbol': symbol,
            'exchange': exchange,
            'bid_pressure': bid_pressure,
            'ask_pressure': ask_pressure,
            'pressure_ratio': bid_pressure / ask_pressure if ask_pressure > 0 else 0,
            'spread': spread,
            'spread_percentage': spread_percentage,
            'top_bid': bids[0][0] if bids else 0,
            'top_ask': asks[0][0] if asks else 0,
            'timestamp': int(time.time() * 1000)
        }


# 全局交易所管理器实例
exchange_manager = ExchangeManager()
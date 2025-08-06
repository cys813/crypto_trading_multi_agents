"""
加密货币数据源实现
"""

import requests
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from pathlib import Path


class BaseDataSource:
    """数据源基类"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化数据源
        
        Args:
            api_key: API密钥
            base_url: 基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def make_request(self, url: str, params: Dict[str, Any] = None, method: str = 'GET') -> Optional[Dict[str, Any]]:
        """
        发起HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            method: 请求方法
            
        Returns:
            响应数据或None
        """
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=params, timeout=30)
            else:
                raise ValueError(f"不支持的请求方法: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return None


class CoinGeckoDataSource(BaseDataSource):
    """CoinGecko数据源"""
    
    def __init__(self, api_key: str = None, demo_mode: bool = True):
        """
        初始化CoinGecko数据源
        
        Args:
            api_key: API密钥
            demo_mode: 演示模式
        """
        super().__init__(api_key, "https://api.coingecko.com/api/v3")
        self.demo_mode = demo_mode
    
    def get_price(self, coin_id: str, vs_currency: str = 'usd') -> Optional[Dict[str, Any]]:
        """
        获取价格数据
        
        Args:
            coin_id: 币种ID
            vs_currency: 计价货币
            
        Returns:
            价格数据
        """
        if self.demo_mode:
            # 演示模式返回模拟数据
            return {
                'coin_id': coin_id,
                'vs_currency': vs_currency,
                'price': 50000.0 if coin_id == 'bitcoin' else 3000.0,
                'price_change_percentage_24h': 2.5,
                'last_updated': datetime.now().isoformat()
            }
        
        url = f"{self.base_url}/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': vs_currency,
            'include_24hr_change': 'true'
        }
        
        return self.make_request(url, params)
    
    def get_market_data(self, coin_id: str, vs_currency: str = 'usd') -> Optional[Dict[str, Any]]:
        """
        获取市场数据
        
        Args:
            coin_id: 币种ID
            vs_currency: 计价货币
            
        Returns:
            市场数据
        """
        if self.demo_mode:
            # 演示模式返回模拟数据
            return {
                'coin_id': coin_id,
                'vs_currency': vs_currency,
                'market_cap': 950000000000,
                'market_cap_rank': 1,
                'total_volume': 25000000000,
                'high_24h': 52000.0,
                'low_24h': 49000.0,
                'price_change_24h': 1000.0,
                'price_change_percentage_24h': 2.0,
                'last_updated': datetime.now().isoformat()
            }
        
        url = f"{self.base_url}/coins/markets"
        params = {
            'vs_currency': vs_currency,
            'ids': coin_id
        }
        
        return self.make_request(url, params)
    
    def get_historical_data(self, coin_id: str, vs_currency: str = 'usd', days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        获取历史数据
        
        Args:
            coin_id: 币种ID
            vs_currency: 计价货币
            days: 天数
            
        Returns:
            历史数据列表
        """
        if self.demo_mode:
            # 演示模式返回模拟数据
            data = []
            base_price = 50000.0 if coin_id == 'bitcoin' else 3000.0
            
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                price = base_price * (1 + (i % 10 - 5) * 0.02)  # 模拟价格波动
                data.append({
                    'timestamp': int(date.timestamp()),
                    'date': date.strftime('%Y-%m-%d'),
                    'price': price
                })
            
            return data
        
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': vs_currency,
            'days': days
        }
        
        result = self.make_request(url, params)
        if result and 'prices' in result:
            return [
                {
                    'timestamp': item[0],
                    'date': datetime.fromtimestamp(item[0] / 1000).strftime('%Y-%m-%d'),
                    'price': item[1]
                }
                for item in result['prices']
            ]
        
        return None


class CoinMarketCapDataSource(BaseDataSource):
    """CoinMarketCap数据源"""
    
    def __init__(self, api_key: str):
        """
        初始化CoinMarketCap数据源
        
        Args:
            api_key: API密钥
        """
        super().__init__(api_key, "https://pro-api.coinmarketcap.com/v1")
        self.session.headers.update({'X-CMC_PRO_API_KEY': api_key})
    
    def get_latest_listings(self, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        获取最新币种列表
        
        Args:
            limit: 限制数量
            
        Returns:
            币种列表数据
        """
        url = f"{self.base_url}/cryptocurrency/listings/latest"
        params = {'limit': limit}
        
        return self.make_request(url, params)
    
    def get_price_data(self, symbol: str, convert: str = 'USD') -> Optional[Dict[str, Any]]:
        """
        获取价格数据
        
        Args:
            symbol: 币种符号
            convert: 转换货币
            
        Returns:
            价格数据
        """
        url = f"{self.base_url}/cryptocurrency/quotes/latest"
        params = {
            'symbol': symbol,
            'convert': convert
        }
        
        return self.make_request(url, params)


class GlassnodeDataSource(BaseDataSource):
    """Glassnode链上数据源"""
    
    def __init__(self, api_key: str):
        """
        初始化Glassnode数据源
        
        Args:
            api_key: API密钥
        """
        super().__init__(api_key, "https://api.glassnode.com/api/v1")
    
    def get_market_data(self, asset: str = 'BTC') -> Optional[Dict[str, Any]]:
        """
        获取市场数据
        
        Args:
            asset: 资产符号
            
        Returns:
            市场数据
        """
        url = f"{self.base_url}/market/price_usd_close"
        params = {
            'a': asset,
            'i': '24h'
        }
        
        return self.make_request(url, params)
    
    def get_onchain_metrics(self, asset: str = 'BTC') -> Optional[Dict[str, Any]]:
        """
        获取链上指标
        
        Args:
            asset: 资产符号
            
        Returns:
            链上指标数据
        """
        metrics = {}
        
        # 获取多个链上指标
        endpoints = [
            ('/addresses/active_count', 'active_addresses'),
            ('/transactions/count', 'transaction_count'),
            ('/distribution/balance_1pct_holders', 'whale_holdings'),
            ('/market/mvrv', 'mvrv_ratio')
        ]
        
        for endpoint, metric_name in endpoints:
            url = f"{self.base_url}{endpoint}"
            params = {'a': asset, 'i': '24h'}
            
            result = self.make_request(url, params)
            if result:
                metrics[metric_name] = result
        
        return metrics if metrics else None


class DeFiLlamaDataSource(BaseDataSource):
    """DeFiLlama DeFi数据源"""
    
    def __init__(self):
        """初始化DeFiLlama数据源"""
        super().__init__(None, "https://api.llama.fi")
    
    def get_tvl_data(self, protocol: str = None) -> Optional[Dict[str, Any]]:
        """
        获取TVL数据
        
        Args:
            protocol: 协议名称（可选）
            
        Returns:
            TVL数据
        """
        if protocol:
            url = f"{self.base_url}/protocol/{protocol}"
        else:
            url = f"{self.base_url}/protocols"
        
        return self.make_request(url)
    
    def get_defi_chains_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取DeFi链数据
        
        Returns:
            DeFi链数据列表
        """
        url = f"{self.base_url}/chains"
        result = self.make_request(url)
        
        return result if isinstance(result, list) else None


class LunarCrushDataSource(BaseDataSource):
    """LunarCrush社交数据源"""
    
    def __init__(self, api_key: str):
        """
        初始化LunarCrush数据源
        
        Args:
            api_key: API密钥
        """
        super().__init__(api_key, "https://api.lunarcrush.com/v2")
    
    def get_social_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取社交指标
        
        Args:
            symbol: 币种符号
            
        Returns:
            社交指标数据
        """
        url = f"{self.base_url}/data"
        params = {
            'symbol': symbol,
            'data': 'assets',
            'key': self.api_key
        }
        
        return self.make_request(url, params)
    
    def get_sentiment_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取情绪数据
        
        Args:
            symbol: 币种符号
            
        Returns:
            情绪数据
        """
        url = f"{self.base_url}/data"
        params = {
            'symbol': symbol,
            'data': 'sentiment',
            'key': self.api_key
        }
        
        return self.make_request(url, params)


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        """初始化数据源管理器"""
        self.data_sources = {}
        self.cache = {}
        self.cache_ttl = 300  # 5分钟缓存
    
    def register_data_source(self, name: str, data_source: BaseDataSource):
        """
        注册数据源
        
        Args:
            name: 数据源名称
            data_source: 数据源实例
        """
        self.data_sources[name] = data_source
    
    def get_data_source(self, name: str) -> Optional[BaseDataSource]:
        """
        获取数据源
        
        Args:
            name: 数据源名称
            
        Returns:
            数据源实例或None
        """
        return self.data_sources.get(name)
    
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
    
    def get_price_data(self, symbol: str, data_source: str = 'coingecko') -> Optional[Dict[str, Any]]:
        """
        获取价格数据
        
        Args:
            symbol: 币种符号
            data_source: 数据源名称
            
        Returns:
            价格数据
        """
        cache_key = f"price_{symbol}_{data_source}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        source = self.get_data_source(data_source)
        if not source:
            return None
        
        if isinstance(source, CoinGeckoDataSource):
            # 转换符号为CoinGecko ID
            coin_id = self._symbol_to_coin_id(symbol)
            if coin_id:
                data = source.get_price(coin_id)
                if data:
                    self.cache_data(cache_key, data)
                    return data
        
        return None
    
    def get_market_data(self, symbol: str, data_source: str = 'coingecko') -> Optional[Dict[str, Any]]:
        """
        获取市场数据
        
        Args:
            symbol: 币种符号
            data_source: 数据源名称
            
        Returns:
            市场数据
        """
        cache_key = f"market_{symbol}_{data_source}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        source = self.get_data_source(data_source)
        if not source:
            return None
        
        if isinstance(source, CoinGeckoDataSource):
            coin_id = self._symbol_to_coin_id(symbol)
            if coin_id:
                data = source.get_market_data(coin_id)
                if data:
                    self.cache_data(cache_key, data)
                    return data
        
        return None
    
    def get_onchain_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取链上数据
        
        Args:
            symbol: 币种符号
            
        Returns:
            链上数据
        """
        cache_key = f"onchain_{symbol}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        source = self.get_data_source('glassnode')
        if source:
            asset = symbol.split('/')[0]  # 获取基础币种
            data = source.get_onchain_metrics(asset)
            if data:
                self.cache_data(cache_key, data)
                return data
        
        return None
    
    def get_sentiment_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取情绪数据
        
        Args:
            symbol: 币种符号
            
        Returns:
            情绪数据
        """
        cache_key = f"sentiment_{symbol}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        source = self.get_data_source('lunarcrush')
        if source:
            asset = symbol.split('/')[0]  # 获取基础币种
            data = source.get_sentiment_data(asset)
            if data:
                self.cache_data(cache_key, data)
                return data
        
        return None
    
    def get_defi_data(self, protocol: str = None) -> Optional[Dict[str, Any]]:
        """
        获取DeFi数据
        
        Args:
            protocol: 协议名称（可选）
            
        Returns:
            DeFi数据
        """
        cache_key = f"defi_{protocol or 'all'}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        source = self.get_data_source('defillama')
        if source:
            data = source.get_tvl_data(protocol)
            if data:
                self.cache_data(cache_key, data)
                return data
        
        return None
    
    def _symbol_to_coin_id(self, symbol: str) -> str:
        """
        将交易对符号转换为CoinGecko ID
        
        Args:
            symbol: 交易对符号
            
        Returns:
            CoinGecko ID
        """
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'MATIC': 'polygon',
            'LINK': 'chainlink'
        }
        
        base_symbol = symbol.split('/')[0]
        return mapping.get(base_symbol, base_symbol.lower())


# 全局数据源管理器实例
data_source_manager = DataSourceManager()
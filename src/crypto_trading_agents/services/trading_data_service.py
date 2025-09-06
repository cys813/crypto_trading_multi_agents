"""
交易数据服务 - 统一的交易数据获取模块

提供标准化的交易数据获取，支持多时间周期数据：
- 最近30天的4小时K线数据
- 最近15天的1小时K线数据  
- 最近3天的15分钟K线数据

所有需要交易数据的模块均从此模块获取数据
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import random
import sys
import os

logger = logging.getLogger(__name__)

class TradingDataService:
    """交易数据服务 - 统一数据获取接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化交易数据服务
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.data_config = config.get("trading_data_config", {})
        
        # 数据源配置
        self.data_source = self.data_config.get("data_source", "mock")  # mock, binance, okx, etc.
        self.base_url = self.data_config.get("base_url", "")
        self.api_key = self.data_config.get("api_key", "")
        self.api_secret = self.data_config.get("api_secret", "")
        
        # 数据缓存
        self.data_cache = {}
        self.cache_expiry = self.data_config.get("cache_expiry", 300)  # 5分钟
        
        # 初始化交易所管理器
        self.exchange_manager = self._initialize_exchange_manager()
        
        logger.info("交易数据服务初始化完成")
    
    def _initialize_exchange_manager(self):
        """初始化交易所管理器"""
        try:
            # 尝试导入现有的交易所管理器
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../data_sources'))
            from exchange_data_sources import exchange_manager
            logger.info("成功导入交易所管理器")
            return exchange_manager
        except Exception as e:
            logger.warning(f"无法导入交易所管理器: {e}，将使用模拟数据")
            return None
    
    def get_trading_data(self, symbol: str, end_date: str = None) -> Dict[str, Any]:
        """
        获取统一的交易数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期，默认为当前日期
            
        Returns:
            统一格式的交易数据
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            logger.info(f"获取交易数据: {symbol}, 截止日期: {end_date}")
            
            # 构建统一的数据结构
            trading_data = {
                "symbol": symbol,
                "end_date": end_date,
                "data_type": "unified_trading_data",
                "timeframes": {},
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "data_source": self.data_source,
                    "api_version": "1.0"
                }
            }
            
            # 获取4小时K线数据 - 最近30天
            kline_4h = self._get_timeframe_data(symbol, "4h", 30, end_dt)
            if kline_4h:
                trading_data["timeframes"]["4h"] = kline_4h
            
            # 获取1小时K线数据 - 最近15天
            kline_1h = self._get_timeframe_data(symbol, "1h", 360, end_dt)
            if kline_1h:
                trading_data["timeframes"]["1h"] = kline_1h
            
            # 获取15分钟K线数据 - 最近3天
            kline_15m = self._get_timeframe_data(symbol, "15m", 288, end_dt)  # 3天 * 24小时 * 4个15分钟
            if kline_15m:
                trading_data["timeframes"]["15m"] = kline_15m
            
            # 添加数据统计信息
            trading_data["statistics"] = self._calculate_statistics(trading_data["timeframes"])
            
            # 添加数据质量评估
            trading_data["data_quality"] = self._assess_data_quality(trading_data["timeframes"])
            
            # 添加市场概览
            trading_data["market_overview"] = self._generate_market_overview(trading_data["timeframes"])
            
            logger.info(f"成功获取交易数据: {symbol}, 时间周期: {list(trading_data['timeframes'].keys())}")
            
            return trading_data
            
        except Exception as e:
            logger.error(f"获取交易数据失败: {e}")
            return {"error": str(e)}
    
    def _get_timeframe_data(self, symbol: str, timeframe: str, limit: int, end_dt: datetime) -> Optional[Dict[str, Any]]:
        """
        获取指定时间周期的数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数据数量限制
            end_dt: 截止时间
            
        Returns:
            时间周期数据
        """
        try:
            # 生成缓存键
            cache_key = f"{symbol}_{timeframe}_{limit}_{end_dt.strftime('%Y-%m-%d')}"
            
            # 检查缓存
            if cache_key in self.data_cache:
                cached_data = self.data_cache[cache_key]
                if datetime.now().timestamp() - cached_data["cached_at"] < self.cache_expiry:
                    logger.debug(f"使用缓存数据: {cache_key}")
                    return cached_data["data"]
            
            # 尝试从真实数据源获取
            kline_data = None
            
            if self.exchange_manager and self.data_source != "mock":
                try:
                    kline_data = self._get_exchange_data(symbol, timeframe, limit, end_dt)
                except Exception as e:
                    logger.warning(f"从交易所获取数据失败: {e}，回退到模拟数据")
            
            # 如果无法获取真实数据，使用模拟数据
            if kline_data is None:
                kline_data = self._generate_mock_data(symbol, timeframe, limit, end_dt)
            
            # 缓存数据
            if kline_data:
                self.data_cache[cache_key] = {
                    "data": kline_data,
                    "cached_at": datetime.now().timestamp()
                }
            
            return kline_data
            
        except Exception as e:
            logger.error(f"获取时间周期数据失败: {timeframe}, {e}")
            return None
    
    def _get_exchange_data(self, symbol: str, timeframe: str, limit: int, end_dt: datetime) -> Dict[str, Any]:
        """
        从交易所获取数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数据数量
            end_dt: 截止时间
            
        Returns:
            交易所数据
        """
        try:
            # 使用交易所管理器获取数据
            ohlcv_data = self.exchange_manager.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                exchange=self.data_source
            )
            
            if ohlcv_data:
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "data": ohlcv_data,
                    "data_count": len(ohlcv_data),
                    "start_time": ohlcv_data[0][0] if ohlcv_data else 0,
                    "end_time": ohlcv_data[-1][0] if ohlcv_data else 0,
                    "source": self.data_source,
                    "retrieved_at": datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"从交易所获取数据失败: {e}")
            return None
    
    def _generate_mock_data(self, symbol: str, timeframe: str, limit: int, end_dt: datetime) -> Dict[str, Any]:
        """
        生成模拟数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数据数量
            end_dt: 截止时间
            
        Returns:
            模拟数据
        """
        try:
            base_currency = symbol.split('/')[0]
            
            # 基础价格设置
            if base_currency == "BTC":
                base_price = 50000
            elif base_currency == "ETH":
                base_price = 3000
            else:
                base_price = 100
            
            # 根据时间周期设置间隔
            timeframe_intervals = {
                "1m": 60,
                "5m": 300,
                "15m": 900,
                "30m": 1800,
                "1h": 3600,
                "4h": 14400,
                "1d": 86400
            }
            
            interval = timeframe_intervals.get(timeframe, 3600)
            
            # 生成K线数据
            ohlcv_data = []
            current_price = base_price
            current_time = end_dt
            
            # 添加一些趋势和波动性
            trend = random.uniform(-0.001, 0.001)  # 每个周期的趋势
            volatility = random.uniform(0.005, 0.02)  # 波动性
            
            for i in range(limit):
                # 生成OHLCV数据
                open_price = current_price
                high_price = open_price * (1 + random.uniform(0, volatility))
                low_price = open_price * (1 - random.uniform(0, volatility))
                close_price = open_price * (1 + trend + random.uniform(-volatility/2, volatility/2))
                volume = random.uniform(1000000, 10000000) * (base_price / 1000)
                
                # 确保价格逻辑正确
                high_price = max(high_price, open_price, close_price, low_price)
                low_price = min(low_price, open_price, close_price, high_price)
                
                ohlcv_data.append([
                    int(current_time.timestamp() * 1000),  # timestamp
                    round(open_price, 2),                   # open
                    round(high_price, 2),                   # high
                    round(low_price, 2),                    # low
                    round(close_price, 2),                  # close
                    int(volume)                             # volume
                ])
                
                current_price = close_price
                current_time -= timedelta(seconds=interval)
            
            # 反转数据，使其按时间顺序排列
            ohlcv_data.reverse()
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "data": ohlcv_data,
                "data_count": len(ohlcv_data),
                "start_time": ohlcv_data[0][0] if ohlcv_data else 0,
                "end_time": ohlcv_data[-1][0] if ohlcv_data else 0,
                "source": "mock",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成模拟数据失败: {e}")
            return {}
    
    def _calculate_statistics(self, timeframes: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算统计信息
        
        Args:
            timeframes: 各时间周期数据
            
        Returns:
            统计信息
        """
        try:
            stats = {
                "timeframes": {},
                "overall": {},
                "price_analysis": {},
                "volume_analysis": {}
            }
            
            all_closes = []
            all_volumes = []
            
            for timeframe, data in timeframes.items():
                ohlcv_data = data.get("data", [])
                if ohlcv_data:
                    closes = [candle[4] for candle in ohlcv_data]
                    volumes = [candle[5] for candle in ohlcv_data]
                    
                    all_closes.extend(closes)
                    all_volumes.extend(volumes)
                    
                    # 单个时间周期统计
                    timeframe_stats = {
                        "price_change": (closes[-1] - closes[0]) / closes[0] if len(closes) > 1 else 0,
                        "volatility": (max(closes) - min(closes)) / closes[0] if closes else 0,
                        "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
                        "high": max(closes) if closes else 0,
                        "low": min(closes) if closes else 0,
                        "data_points": len(closes),
                        "latest_price": closes[-1] if closes else 0
                    }
                    
                    stats["timeframes"][timeframe] = timeframe_stats
            
            # 整体统计
            if all_closes:
                stats["overall"] = {
                    "total_price_change": (all_closes[-1] - all_closes[0]) / all_closes[0] if len(all_closes) > 1 else 0,
                    "overall_volatility": (max(all_closes) - min(all_closes)) / all_closes[0] if all_closes else 0,
                    "total_volume": sum(all_volumes),
                    "avg_volume": sum(all_volumes) / len(all_volumes) if all_volumes else 0,
                    "price_high": max(all_closes),
                    "price_low": min(all_closes),
                    "total_data_points": len(all_closes),
                    "latest_price": all_closes[-1]
                }
                
                # 价格分析
                price_change = stats["overall"]["total_price_change"]
                if price_change > 0.05:
                    price_trend = "strong_uptrend"
                elif price_change > 0.02:
                    price_trend = "uptrend"
                elif price_change < -0.05:
                    price_trend = "strong_downtrend"
                elif price_change < -0.02:
                    price_trend = "downtrend"
                else:
                    price_trend = "sideways"
                
                stats["price_analysis"] = {
                    "trend": price_trend,
                    "change_percent": price_change * 100,
                    "volatility_level": "high" if stats["overall"]["overall_volatility"] > 0.1 else "medium" if stats["overall"]["overall_volatility"] > 0.05 else "low"
                }
                
                # 成交量分析
                recent_volume = sum(all_volumes[-10:]) if len(all_volumes) >= 10 else sum(all_volumes)
                earlier_volume = sum(all_volumes[-20:-10]) if len(all_volumes) >= 20 else recent_volume
                
                if recent_volume > earlier_volume * 1.2:
                    volume_trend = "increasing"
                elif recent_volume < earlier_volume * 0.8:
                    volume_trend = "decreasing"
                else:
                    volume_trend = "stable"
                
                stats["volume_analysis"] = {
                    "trend": volume_trend,
                    "recent_volume": recent_volume,
                    "earlier_volume": earlier_volume,
                    "volume_ratio": recent_volume / earlier_volume if earlier_volume > 0 else 1.0
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"计算统计信息失败: {e}")
            return {}
    
    def _assess_data_quality(self, timeframes: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估数据质量
        
        Args:
            timeframes: 各时间周期数据
            
        Returns:
            数据质量评估
        """
        try:
            quality_scores = {}
            
            for timeframe, data in timeframes.items():
                ohlcv_data = data.get("data", [])
                score = 0.0
                
                if ohlcv_data:
                    # 数据完整性评分
                    expected_count = {
                        "4h": 30,
                        "1h": 360,
                        "15m": 288
                    }.get(timeframe, len(ohlcv_data))
                    
                    completeness = len(ohlcv_data) / expected_count
                    score += completeness * 0.4
                    
                    # 数据一致性评分
                    if len(ohlcv_data) > 1:
                        timestamps = [candle[0] for candle in ohlcv_data]
                        time_gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                        consistency = 1.0 if len(set(time_gaps)) == 1 else 0.8
                        score += consistency * 0.3
                    
                    # 数据合理性评分
                    prices = [candle[4] for candle in ohlcv_data]
                    if prices:
                        price_range = max(prices) - min(prices)
                        avg_price = sum(prices) / len(prices)
                        reasonableness = 1.0 if price_range / avg_price < 0.5 else 0.7
                        score += reasonableness * 0.3
                
                quality_scores[timeframe] = min(score, 1.0)
            
            # 整体质量评分
            overall_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.0
            
            return {
                "overall_quality": overall_quality,
                "quality_level": "excellent" if overall_quality > 0.9 else "good" if overall_quality > 0.7 else "fair" if overall_quality > 0.5 else "poor",
                "timeframe_scores": quality_scores,
                "recommendations": self._generate_quality_recommendations(quality_scores)
            }
            
        except Exception as e:
            logger.error(f"评估数据质量失败: {e}")
            return {"overall_quality": 0.0, "quality_level": "unknown"}
    
    def _generate_quality_recommendations(self, quality_scores: Dict[str, float]) -> List[str]:
        """
        生成数据质量改进建议
        
        Args:
            quality_scores: 各时间周期质量评分
            
        Returns:
            改进建议列表
        """
        recommendations = []
        
        for timeframe, score in quality_scores.items():
            if score < 0.5:
                recommendations.append(f"{timeframe}时间周期数据质量较差，建议重新获取")
            elif score < 0.7:
                recommendations.append(f"{timeframe}时间周期数据质量一般，建议检查数据完整性")
        
        if not recommendations:
            recommendations.append("数据质量良好，可以用于分析")
        
        return recommendations
    
    def _generate_market_overview(self, timeframes: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成市场概览
        
        Args:
            timeframes: 各时间周期数据
            
        Returns:
            市场概览
        """
        try:
            overview = {
                "timeframe_signals": {},
                "market_regime": "unknown",
                "volatility_regime": "unknown",
                "liquidity_status": "unknown"
            }
            
            # 分析各时间周期的信号
            for timeframe, data in timeframes.items():
                ohlcv_data = data.get("data", [])
                if ohlcv_data:
                    closes = [candle[4] for candle in ohlcv_data]
                    volumes = [candle[5] for candle in ohlcv_data]
                    
                    # 简单的趋势分析
                    if len(closes) >= 20:
                        ma20 = sum(closes[-20:]) / 20
                        current_price = closes[-1]
                        
                        if current_price > ma20 * 1.02:
                            signal = "bullish"
                        elif current_price < ma20 * 0.98:
                            signal = "bearish"
                        else:
                            signal = "neutral"
                        
                        overview["timeframe_signals"][timeframe] = {
                            "signal": signal,
                            "strength": abs(current_price - ma20) / ma20
                        }
            
            # 确定市场状态
            signals = [info["signal"] for info in overview["timeframe_signals"].values()]
            if signals:
                bullish_count = signals.count("bullish")
                bearish_count = signals.count("bearish")
                
                if bullish_count > bearish_count:
                    overview["market_regime"] = "bullish"
                elif bearish_count > bullish_count:
                    overview["market_regime"] = "bearish"
                else:
                    overview["market_regime"] = "neutral"
            
            return overview
            
        except Exception as e:
            logger.error(f"生成市场概览失败: {e}")
            return {}
    
    def get_data_summary(self, symbol: str) -> Dict[str, Any]:
        """
        获取数据摘要
        
        Args:
            symbol: 交易对符号
            
        Returns:
            数据摘要
        """
        try:
            # 获取交易数据
            trading_data = self.get_trading_data(symbol)
            
            if "error" in trading_data:
                return {"error": trading_data["error"]}
            
            # 生成摘要
            summary = {
                "symbol": symbol,
                "end_date": trading_data.get("end_date"),
                "available_timeframes": list(trading_data.get("timeframes", {}).keys()),
                "data_quality": trading_data.get("data_quality", {}),
                "statistics": trading_data.get("statistics", {}),
                "market_overview": trading_data.get("market_overview", {}),
                "latest_prices": {}
            }
            
            # 提取最新价格
            for timeframe, data in trading_data.get("timeframes", {}).items():
                ohlcv_data = data.get("data", [])
                if ohlcv_data:
                    latest_candle = ohlcv_data[-1]
                    summary["latest_prices"][timeframe] = {
                        "timestamp": latest_candle[0],
                        "open": latest_candle[1],
                        "high": latest_candle[2],
                        "low": latest_candle[3],
                        "close": latest_candle[4],
                        "volume": latest_candle[5]
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取数据摘要失败: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """清除数据缓存"""
        self.data_cache.clear()
        logger.info("交易数据缓存已清除")
    
    def get_supported_timeframes(self) -> List[str]:
        """
        获取支持的时间周期
        
        Returns:
            支持的时间周期列表
        """
        return ["4h", "1h", "15m"]
    
    def get_data_source_info(self) -> Dict[str, Any]:
        """
        获取数据源信息
        
        Returns:
            数据源信息
        """
        return {
            "data_source": self.data_source,
            "cache_enabled": True,
            "cache_expiry": self.cache_expiry,
            "supported_timeframes": self.get_supported_timeframes(),
            "api_available": self.exchange_manager is not None
        }

class MarketMicrostructureDataService:
    """市场微观结构数据服务 - 专门为做市商分析提供深度市场数据"""
    
    def __init__(self, config: Dict[str, Any], trading_data_service: TradingDataService):
        """
        初始化市场微观结构数据服务
        
        Args:
            config: 配置字典
            trading_data_service: 基础交易数据服务
        """
        self.config = config
        self.trading_data_service = trading_data_service
        self.microstructure_config = config.get("microstructure_config", {})
        
        # 数据源配置
        self.data_source = self.microstructure_config.get("data_source", "mock")
        self.orderbook_depth = self.microstructure_config.get("orderbook_depth", 20)
        self.tick_data_limit = self.microstructure_config.get("tick_data_limit", 1000)
        
        # 缓存配置
        self.cache = {}
        self.cache_expiry = self.microstructure_config.get("cache_expiry", 60)  # 1分钟缓存
        
        logger.info("市场微观结构数据服务初始化完成")
    
    async def collect_market_microstructure_data(self, symbol: str, end_date: str = None) -> Dict[str, Any]:
        """
        收集市场微观结构数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            市场微观结构数据
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"收集市场微观结构数据: {symbol}, 截止日期: {end_date}")
            
            # 并行获取各类市场微观结构数据
            orderbook_data = await self._get_orderbook_data(symbol)
            tick_data = await self._get_tick_data(symbol)
            volume_profile = await self._get_volume_profile_data(symbol)
            liquidity_metrics = await self._get_liquidity_metrics(symbol)
            market_impact_data = await self._get_market_impact_data(symbol)
            
            microstructure_data = {
                "symbol": symbol,
                "start_date": (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"),
                "end_date": end_date,
                "data_source": self.data_source,
                "collected_at": datetime.now().isoformat(),
                "order_book_data": orderbook_data,
                "tick_data": tick_data,
                "volume_profile": volume_profile,
                "liquidity_metrics": liquidity_metrics,
                "market_impact_data": market_impact_data,
                "data_quality": self._assess_microstructure_data_quality({
                    "order_book_data": orderbook_data,
                    "tick_data": tick_data,
                    "volume_profile": volume_profile,
                    "liquidity_metrics": liquidity_metrics,
                    "market_impact_data": market_impact_data
                })
            }
            
            logger.info(f"成功收集市场微观结构数据: {symbol}")
            return microstructure_data
            
        except Exception as e:
            logger.error(f"收集市场微观结构数据失败: {symbol}, {e}")
            return {"error": str(e)}
    
    async def _get_orderbook_data(self, symbol: str) -> Dict[str, Any]:
        """获取订单簿数据"""
        try:
            cache_key = f"orderbook_{symbol}"
            
            # 检查缓存
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 尝试从真实数据源获取
            if self.data_source != "mock":
                real_data = await self._get_real_orderbook_data(symbol)
                if real_data:
                    self._cache_data(cache_key, real_data)
                    return real_data
            
            # 生成模拟数据
            mock_data = self._generate_mock_orderbook_data(symbol)
            self._cache_data(cache_key, mock_data)
            return mock_data
            
        except Exception as e:
            logger.error(f"获取订单簿数据失败: {e}")
            return self._generate_mock_orderbook_data(symbol)
    
    async def _get_real_orderbook_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从真实数据源获取订单簿数据"""
        try:
            # 如果有交易所管理器，尝试获取真实数据
            if hasattr(self.trading_data_service, 'exchange_manager') and self.trading_data_service.exchange_manager:
                # 这里可以扩展支持不同的交易所API
                # 目前先返回None，回退到模拟数据
                pass
            
            return None
            
        except Exception as e:
            logger.warning(f"获取真实订单簿数据失败: {e}")
            return None
    
    def _generate_mock_orderbook_data(self, symbol: str) -> Dict[str, Any]:
        """生成模拟订单簿数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        # 生成买单和卖单
        bids = []
        asks = []
        
        for i in range(self.orderbook_depth):
            # 买单价格递减，卖单价格递增
            bid_price = base_price * (1 - 0.001 * (i + 1))
            ask_price = base_price * (1 + 0.001 * (i + 1))
            
            # 数量随深度衰减，添加一些随机性
            base_quantity = base_price * 0.1 * (1 - i * 0.03)
            bid_quantity = base_quantity * (0.8 + random.random() * 0.4)
            ask_quantity = base_quantity * (0.8 + random.random() * 0.4)
            
            bids.append({
                "price": round(bid_price, 2),
                "quantity": round(bid_quantity, 6),
                "total": sum(bid["quantity"] for bid in bids) + bid_quantity,
                "order_count": random.randint(1, 10)
            })
            
            asks.append({
                "price": round(ask_price, 2),
                "quantity": round(ask_quantity, 6),
                "total": sum(ask["quantity"] for ask in asks) + ask_quantity,
                "order_count": random.randint(1, 10)
            })
        
        # 计算加权中间价
        best_bid = bids[0]
        best_ask = asks[0]
        weighted_mid_price = (best_bid["price"] * best_ask["quantity"] + best_ask["price"] * best_bid["quantity"]) / (best_bid["quantity"] + best_ask["quantity"])
        
        return {
            "bids": bids,
            "asks": asks,
            "spread": best_ask["price"] - best_bid["price"],
            "spread_percentage": (best_ask["price"] - best_bid["price"]) / base_price * 100,
            "total_bid_depth": sum(bid["quantity"] for bid in bids),
            "total_ask_depth": sum(ask["quantity"] for ask in asks),
            "mid_price": (best_bid["price"] + best_ask["price"]) / 2,
            "weighted_mid_price": weighted_mid_price,
            "timestamp": datetime.now().isoformat(),
            "depth_levels": len(bids)
        }
    
    async def _get_tick_data(self, symbol: str) -> Dict[str, Any]:
        """获取逐笔交易数据"""
        try:
            cache_key = f"ticks_{symbol}"
            
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 尝试获取真实tick数据
            if self.data_source != "mock":
                real_data = await self._get_real_tick_data(symbol)
                if real_data:
                    self._cache_data(cache_key, real_data)
                    return real_data
            
            # 生成模拟数据
            mock_data = self._generate_mock_tick_data(symbol)
            self._cache_data(cache_key, mock_data)
            return mock_data
            
        except Exception as e:
            logger.error(f"获取逐笔交易数据失败: {e}")
            return self._generate_mock_tick_data(symbol)
    
    async def _get_real_tick_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从真实数据源获取逐笔交易数据"""
        try:
            # 这里可以集成真实的tick数据API
            # 比如WebSocket实时数据或者REST API历史数据
            return None
            
        except Exception as e:
            logger.warning(f"获取真实tick数据失败: {e}")
            return None
    
    def _generate_mock_tick_data(self, symbol: str) -> Dict[str, Any]:
        """生成模拟逐笔交易数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        trades = []
        current_time = datetime.now()
        current_price = base_price
        
        # 生成交易数据，模拟真实的价格波动
        for i in range(self.tick_data_limit):
            # 价格随机游走
            price_change = random.gauss(0, base_price * 0.0001)  # 正态分布的价格变化
            current_price = max(current_price + price_change, base_price * 0.8)  # 防止价格过低
            
            # 交易数量
            quantity = random.uniform(base_price * 0.0001, base_price * 0.01)
            
            # 买卖方向，略微倾向于保持趋势
            side = "buy" if random.random() > 0.5 else "sell"
            
            # 交易时间（倒序）
            trade_time = current_time - timedelta(seconds=i * random.uniform(0.1, 5))
            
            trades.append({
                "timestamp": trade_time.isoformat(),
                "trade_id": f"T{i+1:06d}",
                "price": round(current_price, 2),
                "quantity": round(quantity, 6),
                "side": side,
                "taker_side": side,  # 主动方
                "fee_currency": symbol.split('/')[1],
                "fee": round(quantity * current_price * 0.001, 4)  # 0.1% 手续费
            })
        
        # 按时间排序（最新的在前）
        trades.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 计算统计数据
        total_volume = sum(trade["quantity"] for trade in trades)
        buy_volume = sum(trade["quantity"] for trade in trades if trade["side"] == "buy")
        sell_volume = total_volume - buy_volume
        
        return {
            "trades": trades,
            "total_volume": round(total_volume, 6),
            "buy_volume": round(buy_volume, 6),
            "sell_volume": round(sell_volume, 6),
            "trade_count": len(trades),
            "average_trade_size": round(total_volume / len(trades), 6) if trades else 0,
            "buy_sell_ratio": round(buy_volume / sell_volume, 3) if sell_volume > 0 else 1.0,
            "time_range": {
                "start": trades[-1]["timestamp"] if trades else None,
                "end": trades[0]["timestamp"] if trades else None
            },
            "price_range": {
                "high": max(trade["price"] for trade in trades) if trades else 0,
                "low": min(trade["price"] for trade in trades) if trades else 0,
                "latest": trades[0]["price"] if trades else 0
            }
        }
    
    async def _get_volume_profile_data(self, symbol: str) -> Dict[str, Any]:
        """获取成交量分布数据"""
        try:
            cache_key = f"volume_profile_{symbol}"
            
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 生成成交量分布数据
            volume_profile = self._generate_volume_profile_data(symbol)
            self._cache_data(cache_key, volume_profile)
            return volume_profile
            
        except Exception as e:
            logger.error(f"获取成交量分布数据失败: {e}")
            return self._generate_volume_profile_data(symbol)
    
    def _generate_volume_profile_data(self, symbol: str) -> Dict[str, Any]:
        """生成成交量分布数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        price_levels = []
        
        # 创建价格区间和对应的成交量
        num_levels = 50  # 50个价格层级
        price_range = base_price * 0.1  # ±10% 价格范围
        
        for i in range(num_levels):
            # 价格层级
            price_offset = (i - num_levels//2) * (price_range * 2 / num_levels)
            price_level = base_price + price_offset
            
            # 成交量分布（中间价格成交量更大）
            distance_from_center = abs(i - num_levels//2) / (num_levels//2)
            volume_multiplier = max(0.1, 1 - distance_from_center * 0.8)  # 高斯分布近似
            
            base_volume = base_price * 0.05
            volume = base_volume * volume_multiplier * (0.5 + random.random())
            buy_volume = volume * (0.3 + random.random() * 0.4)  # 30%-70%买单
            sell_volume = volume - buy_volume
            
            price_levels.append({
                "price": round(price_level, 2),
                "volume": round(volume, 6),
                "buy_volume": round(buy_volume, 6),
                "sell_volume": round(sell_volume, 6),
                "trade_count": int(volume / (base_price * 0.001)),
                "volume_percentage": 0  # 后续计算
            })
        
        # 计算成交量百分比
        total_volume = sum(level["volume"] for level in price_levels)
        for level in price_levels:
            level["volume_percentage"] = round(level["volume"] / total_volume * 100, 2)
        
        # 找到POC（Point of Control）- 成交量最大的价格
        poc_level = max(price_levels, key=lambda x: x["volume"])
        
        # 计算价值区域（包含68%成交量的价格区间）
        sorted_levels = sorted(price_levels, key=lambda x: x["volume"], reverse=True)
        cumulative_volume = 0
        value_area_levels = []
        
        for level in sorted_levels:
            cumulative_volume += level["volume"]
            value_area_levels.append(level)
            if cumulative_volume >= total_volume * 0.68:
                break
        
        value_area_high = max(level["price"] for level in value_area_levels)
        value_area_low = min(level["price"] for level in value_area_levels)
        
        return {
            "price_levels": price_levels,
            "point_of_control": poc_level["price"],
            "poc_volume": poc_level["volume"],
            "value_area": {
                "high": value_area_high,
                "low": value_area_low,
                "volume_percentage": 68.0
            },
            "total_volume": round(total_volume, 6),
            "volume_distribution": "normal",
            "analysis": {
                "skewness": random.uniform(-0.5, 0.5),  # 偏度
                "kurtosis": random.uniform(2.5, 4.0),   # 峰度
                "concentration_ratio": poc_level["volume_percentage"] / 2  # 集中度
            }
        }
    
    async def _get_liquidity_metrics(self, symbol: str) -> Dict[str, Any]:
        """获取流动性指标"""
        try:
            cache_key = f"liquidity_{symbol}"
            
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 获取基础价格和订单簿数据来计算流动性指标
            orderbook = await self._get_orderbook_data(symbol)
            liquidity_data = self._calculate_liquidity_metrics(symbol, orderbook)
            
            self._cache_data(cache_key, liquidity_data)
            return liquidity_data
            
        except Exception as e:
            logger.error(f"获取流动性指标失败: {e}")
            return self._generate_mock_liquidity_metrics(symbol)
    
    def _calculate_liquidity_metrics(self, symbol: str, orderbook: Dict[str, Any]) -> Dict[str, Any]:
        """基于订单簿计算流动性指标"""
        try:
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])
            base_price = orderbook.get("mid_price", 50000 if "BTC" in symbol else 3000)
            
            # 计算不同规模订单的流动性指标
            test_sizes = [
                {"name": "100_usd", "size": 100},
                {"name": "1k_usd", "size": 1000},
                {"name": "10k_usd", "size": 10000},
                {"name": "100k_usd", "size": 100000},
                {"name": "1m_usd", "size": 1000000}
            ]
            
            liquidity_metrics = {}
            
            for test_size in test_sizes:
                size_usd = test_size["size"]
                size_name = test_size["name"]
                
                # 计算买单流动性（需要卖出这么多USD的价格冲击）
                buy_impact = self._calculate_market_impact(asks, size_usd, "buy", base_price)
                
                # 计算卖单流动性（需要买入这么多USD的价格冲击）
                sell_impact = self._calculate_market_impact(bids, size_usd, "sell", base_price)
                
                liquidity_metrics[size_name] = {
                    "buy_impact": buy_impact,
                    "sell_impact": sell_impact,
                    "average_impact": (buy_impact + sell_impact) / 2,
                    "liquidity_score": max(0, 1 - (buy_impact + sell_impact) / 2)  # 0-1分数
                }
            
            # 计算整体流动性评分
            overall_scores = [metrics["liquidity_score"] for metrics in liquidity_metrics.values()]
            overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
            
            # 流动性质量评级
            if overall_score > 0.9:
                quality = "excellent"
            elif overall_score > 0.8:
                quality = "good"
            elif overall_score > 0.6:
                quality = "fair"
            else:
                quality = "poor"
            
            return {
                "size_impact_analysis": liquidity_metrics,
                "overall_liquidity_score": round(overall_score, 3),
                "liquidity_quality": quality,
                "depth_analysis": {
                    "bid_depth_5": sum(bid["quantity"] for bid in bids[:5]) if len(bids) >= 5 else 0,
                    "ask_depth_5": sum(ask["quantity"] for ask in asks[:5]) if len(asks) >= 5 else 0,
                    "bid_depth_10": sum(bid["quantity"] for bid in bids[:10]) if len(bids) >= 10 else 0,
                    "ask_depth_10": sum(ask["quantity"] for ask in asks[:10]) if len(asks) >= 10 else 0
                },
                "spread_analysis": {
                    "bid_ask_spread": orderbook.get("spread", 0),
                    "spread_percentage": orderbook.get("spread_percentage", 0),
                    "effective_spread": orderbook.get("spread", 0) * 1.1  # 考虑实际交易成本
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"计算流动性指标失败: {e}")
            return self._generate_mock_liquidity_metrics(symbol)
    
    def _calculate_market_impact(self, orders: List[Dict], size_usd: float, side: str, base_price: float) -> float:
        """计算市场冲击"""
        try:
            remaining_size = size_usd
            total_cost = 0
            
            for order in orders:
                if remaining_size <= 0:
                    break
                
                order_price = order["price"]
                order_quantity = order["quantity"]
                order_value = order_price * order_quantity
                
                if order_value >= remaining_size:
                    # 这个订单就足够了
                    needed_quantity = remaining_size / order_price
                    total_cost += remaining_size
                    remaining_size = 0
                else:
                    # 需要吃掉整个订单
                    total_cost += order_value
                    remaining_size -= order_value
            
            if remaining_size > 0:
                # 订单簿深度不够，返回高冲击
                return 0.1  # 10%冲击
            
            # 计算平均价格和冲击
            average_price = total_cost / (size_usd / base_price)  # 平均成交价格
            
            if side == "buy":
                impact = (average_price - base_price) / base_price
            else:
                impact = (base_price - average_price) / base_price
            
            return max(0, impact)
            
        except Exception as e:
            logger.error(f"计算市场冲击失败: {e}")
            return 0.05  # 默认5%冲击
    
    def _generate_mock_liquidity_metrics(self, symbol: str) -> Dict[str, Any]:
        """生成模拟流动性指标"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        # 模拟不同规模订单的流动性指标
        size_impacts = {
            "100_usd": {"buy_impact": 0.0005, "sell_impact": 0.0005},
            "1k_usd": {"buy_impact": 0.002, "sell_impact": 0.002},
            "10k_usd": {"buy_impact": 0.005, "sell_impact": 0.006},
            "100k_usd": {"buy_impact": 0.015, "sell_impact": 0.018},
            "1m_usd": {"buy_impact": 0.045, "sell_impact": 0.055}
        }
        
        for size_name in size_impacts:
            impact_data = size_impacts[size_name]
            impact_data["average_impact"] = (impact_data["buy_impact"] + impact_data["sell_impact"]) / 2
            impact_data["liquidity_score"] = max(0, 1 - impact_data["average_impact"] * 10)
        
        overall_score = sum(data["liquidity_score"] for data in size_impacts.values()) / len(size_impacts)
        
        return {
            "size_impact_analysis": size_impacts,
            "overall_liquidity_score": round(overall_score, 3),
            "liquidity_quality": "excellent" if overall_score > 0.9 else "good",
            "depth_analysis": {
                "bid_depth_5": base_price * 2.5,
                "ask_depth_5": base_price * 2.8,
                "bid_depth_10": base_price * 5.2,
                "ask_depth_10": base_price * 5.8
            },
            "spread_analysis": {
                "bid_ask_spread": base_price * 0.0002,
                "spread_percentage": 0.02,
                "effective_spread": base_price * 0.00025
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_market_impact_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场冲击数据"""
        try:
            cache_key = f"market_impact_{symbol}"
            
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # 生成市场冲击数据
            impact_data = self._generate_market_impact_data(symbol)
            self._cache_data(cache_key, impact_data)
            return impact_data
            
        except Exception as e:
            logger.error(f"获取市场冲击数据失败: {e}")
            return self._generate_market_impact_data(symbol)
    
    def _generate_market_impact_data(self, symbol: str) -> Dict[str, Any]:
        """生成市场冲击数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        # 生成不同规模的市场冲击曲线
        impact_curve = []
        sizes = [100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]  # USD
        
        for size in sizes:
            # 市场冲击通常与订单规模的平方根成正比
            base_impact = 0.0001 * (size ** 0.5) / (base_price ** 0.3)
            
            # 添加一些随机性
            buy_impact = base_impact * (0.8 + random.random() * 0.4)
            sell_impact = base_impact * (0.8 + random.random() * 0.4)
            
            impact_curve.append({
                "size_usd": size,
                "size_base": round(size / base_price, 6),
                "buy_impact": round(buy_impact, 6),
                "sell_impact": round(sell_impact, 6),
                "average_impact": round((buy_impact + sell_impact) / 2, 6)
            })
        
        return {
            "impact_curve": impact_curve,
            "impact_model": {
                "coefficient": 0.0002,
                "exponent": 0.5,
                "base_spread": base_price * 0.0001
            },
            "recovery_times": {
                "small_orders": random.randint(1, 3),      # 1-3分钟
                "medium_orders": random.randint(3, 10),     # 3-10分钟
                "large_orders": random.randint(10, 30)      # 10-30分钟
            },
            "permanent_vs_temporary": {
                "permanent_ratio": 0.3,  # 30%永久冲击
                "temporary_ratio": 0.7   # 70%临时冲击
            },
            "liquidity_regeneration": {
                "half_life_minutes": 5,
                "full_recovery_minutes": 15
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]["cached_at"]
        return (datetime.now().timestamp() - cached_time) < self.cache_expiry
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any]):
        """缓存数据"""
        self.cache[cache_key] = {
            "data": data,
            "cached_at": datetime.now().timestamp()
        }
    
    def _assess_microstructure_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估微观结构数据质量"""
        try:
            quality_scores = {}
            
            # 评估各类数据的质量
            data_types = ["order_book_data", "tick_data", "volume_profile", "liquidity_metrics", "market_impact_data"]
            
            for data_type in data_types:
                type_data = data.get(data_type, {})
                if not type_data or "error" in type_data:
                    quality_scores[data_type] = 0.0
                elif type_data.get("data_source") == "mock":
                    quality_scores[data_type] = 0.7  # 模拟数据质量中等
                else:
                    quality_scores[data_type] = 0.95  # 真实数据质量高
            
            overall_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.0
            
            return {
                "overall_quality": round(overall_quality, 3),
                "data_type_scores": quality_scores,
                "quality_level": "excellent" if overall_quality > 0.9 else "good" if overall_quality > 0.7 else "fair",
                "data_freshness": "real_time" if self.data_source != "mock" else "simulated",
                "assessment_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"评估数据质量失败: {e}")
            return {"overall_quality": 0.5, "quality_level": "unknown"}

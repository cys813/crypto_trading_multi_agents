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
"""
K线数据服务 - 提供标准化的K线数据收集和处理

支持多时间周期K线数据的获取、格式化和预处理
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class KlineDataService:
    """K线数据服务"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化K线数据服务
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.data_config = config.get("kline_data_config", {})
        
        # 数据源配置
        self.data_source = self.data_config.get("data_source", "mock")  # mock, binance, okx, etc.
        self.base_url = self.data_config.get("base_url", "")
        self.api_key = self.data_config.get("api_key", "")
        self.api_secret = self.data_config.get("api_secret", "")
        
        # 数据缓存
        self.data_cache = {}
        self.cache_expiry = self.data_config.get("cache_expiry", 300)  # 5分钟
        
    def collect_multi_timeframe_kline_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集多时间周期K线数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            多时间周期K线数据
        """
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # 收集不同时间周期的数据
            kline_data = {
                "symbol": symbol,
                "end_date": end_date,
                "data_type": "multi_timeframe",
                "timeframes": {}
            }
            
            # 4小时K线 - 最近30个
            kline_4h = self._get_kline_data(symbol, "4h", 30, end_dt)
            if kline_4h:
                kline_data["timeframes"]["4h"] = kline_4h
            
            # 1小时K线 - 最近15天 = 360个
            kline_1h = self._get_kline_data(symbol, "1h", 360, end_dt)
            if kline_1h:
                kline_data["timeframes"]["1h"] = kline_1h
            
            # 3小时K线 - 最近3天 = 24个
            kline_3h = self._get_kline_data(symbol, "3h", 24, end_dt)
            if kline_3h:
                kline_data["timeframes"]["3h"] = kline_3h
            
            # 添加数据统计信息
            kline_data["statistics"] = self._calculate_multi_timeframe_statistics(kline_data["timeframes"])
            
            # 添加数据质量信息
            kline_data["data_quality"] = self._assess_data_quality(kline_data["timeframes"])
            
            logger.info(f"成功收集多时间周期K线数据: {symbol}, 时间周期: {list(kline_data['timeframes'].keys())}")
            
            return kline_data
            
        except Exception as e:
            logger.error(f"收集多时间周期K线数据失败: {e}")
            return {"error": str(e)}
    
    def _get_kline_data(self, symbol: str, timeframe: str, limit: int, end_dt: datetime) -> Optional[Dict[str, Any]]:
        """
        获取指定时间周期的K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数据数量
            end_dt: 截止时间
            
        Returns:
            K线数据
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
            
            # 根据数据源获取数据
            if self.data_source == "mock":
                kline_data = self._generate_mock_kline_data(symbol, timeframe, limit, end_dt)
            elif self.data_source == "binance":
                kline_data = self._get_binance_kline_data(symbol, timeframe, limit, end_dt)
            else:
                logger.warning(f"不支持的数据源: {self.data_source}")
                return None
            
            # 缓存数据
            if kline_data:
                self.data_cache[cache_key] = {
                    "data": kline_data,
                    "cached_at": datetime.now().timestamp()
                }
            
            return kline_data
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {timeframe}, {e}")
            return None
    
    def _generate_mock_kline_data(self, symbol: str, timeframe: str, limit: int, end_dt: datetime) -> Dict[str, Any]:
        """
        生成模拟K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数据数量
            end_dt: 截止时间
            
        Returns:
            模拟K线数据
        """
        try:
            base_currency = symbol.split('/')[0]
            quote_currency = symbol.split('/')[1] if '/' in symbol else 'USDT'
            
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
                "3h": 10800,
                "4h": 14400,
                "1d": 86400
            }
            
            interval = timeframe_intervals.get(timeframe, 3600)
            
            # 生成K线数据
            ohlcv_data = []
            current_price = base_price
            current_time = end_dt
            
            # 添加一些趋势和波动性
            trend = random.uniform(-0.002, 0.002)  # 每个周期的趋势
            volatility = random.uniform(0.01, 0.05)  # 波动性
            
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
            logger.error(f"生成模拟K线数据失败: {e}")
            return {}
    
    def _get_binance_kline_data(self, symbol: str, timeframe: str, limit: int, end_dt: datetime) -> Dict[str, Any]:
        """
        从Binance获取K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 数据数量
            end_dt: 截止时间
            
        Returns:
            Binance K线数据
        """
        # 这里应该是真实的Binance API调用
        # 由于没有真实的API配置，返回空字典
        logger.warning("Binance API调用未实现，使用模拟数据")
        return self._generate_mock_kline_data(symbol, timeframe, limit, end_dt)
    
    def _calculate_multi_timeframe_statistics(self, timeframes: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算多时间周期统计信息
        
        Args:
            timeframes: 各时间周期数据
            
        Returns:
            统计信息
        """
        try:
            stats = {
                "timeframes": {},
                "overall": {}
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
                        "data_points": len(closes)
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
                    "total_data_points": len(all_closes)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"计算多时间周期统计信息失败: {e}")
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
                    completeness = len(ohlcv_data) / data.get("data_count", 1)
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
    
    def get_latest_kline_summary(self, symbol: str) -> Dict[str, Any]:
        """
        获取最新的K线数据摘要
        
        Args:
            symbol: 交易对符号
            
        Returns:
            K线数据摘要
        """
        try:
            # 获取当前时间
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # 收集数据
            kline_data = self.collect_multi_timeframe_kline_data(symbol, end_date)
            
            if "error" in kline_data:
                return {"error": kline_data["error"]}
            
            # 生成摘要
            summary = {
                "symbol": symbol,
                "end_date": end_date,
                "available_timeframes": list(kline_data.get("timeframes", {}).keys()),
                "data_quality": kline_data.get("data_quality", {}),
                "statistics": kline_data.get("statistics", {}),
                "latest_prices": {}
            }
            
            # 提取最新价格
            for timeframe, data in kline_data.get("timeframes", {}).items():
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
            logger.error(f"获取K线数据摘要失败: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """清除数据缓存"""
        self.data_cache.clear()
        logger.info("K线数据缓存已清除")
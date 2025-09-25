"""
技术分析师 - 专注加密货币技术分析

基于原版技术分析，针对加密货币市场特性优化
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import numpy as np

# 导入AI增强技术分析器
from .ai_technical_analyzer import AITechnicalAnalyzer
# 导入新的交易数据服务
from ...services.trading_data_service import TradingDataService

logger = logging.getLogger(__name__)

class TechnicalAnalyst:
    """加密货币技术分析师"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化技术分析师
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.indicators = config.get("analysis_config", {}).get("technical_indicators", [])
        
        # 技术分析权重配置
        self.indicator_weights = {
            "rsi": 0.15,
            "macd": 0.20,
            "bollinger_bands": 0.15,
            "ichimoku": 0.25,
            "stochastic": 0.10,
            "williams_r": 0.10,
            "volume": 0.05,
        }
        
        # 初始化新的交易数据服务
        self.trading_data_service = TradingDataService(config)
        
        # 初始化AI增强分析器
        self.ai_analyzer = None
        self._initialize_ai_analyzer()
    
    
    
    def _initialize_ai_analyzer(self):
        """初始化AI增强分析器"""
        try:
            ai_config = self.config.get("ai_analysis_config", {})
            if ai_config.get("enabled", True):
                self.ai_analyzer = AITechnicalAnalyzer(self.config)
                logger.info("AI增强技术分析器初始化成功")
            else:
                logger.info("AI增强分析功能已禁用")
        except Exception as e:
            logger.error(f"初始化AI增强分析器失败: {e}")
            self.ai_analyzer = None
    
    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集技术分析数据 - 使用新的统一交易数据服务
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            技术分析数据
        """
        try:
            logger.info(f"使用新的交易数据服务获取技术分析数据: {symbol}")
            
            # 使用新的交易数据服务获取数据
            trading_data = self.trading_data_service.get_trading_data(symbol, end_date)
            
            if "error" in trading_data:
                logger.error(f"获取交易数据失败: {trading_data['error']}")
                return {"error": trading_data["error"]}
            
            # 提取各时间周期数据
            timeframes = trading_data.get("timeframes", {})
            
            if not timeframes:
                logger.warning(f"没有可用的时间周期数据: {symbol}")
                return {"error": "No timeframe data available"}
            
            # 计算各时间周期的技术指标
            indicators = {}
            volume_profiles = {}
            market_structures = {}
            
            for timeframe_name, timeframe_data in timeframes.items():
                ohlcv_data = timeframe_data.get("data", [])
                if ohlcv_data:
                    # 计算技术指标
                    timeframe_indicators = self._calculate_timeframe_indicators(ohlcv_data)
                    indicators[timeframe_name] = timeframe_indicators
                    
                    # 分析成交量分布
                    volume_profile = self._analyze_timeframe_volume_profile(ohlcv_data)
                    volume_profiles[timeframe_name] = volume_profile
                    
                    # 分析市场结构
                    market_structure = self._analyze_timeframe_market_structure(ohlcv_data)
                    market_structures[timeframe_name] = market_structure
            
            # 计算跨时间周期综合指标
            cross_timeframe_indicators = self._calculate_cross_timeframe_indicators(indicators)
            
            # 构建返回数据
            start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
            
            return {
                "symbol": symbol,
                "timeframe": "multi_timeframe",
                "start_date": start_date,
                "end_date": end_date,
                "trading_data": trading_data,
                "indicators": indicators,
                "cross_timeframe_indicators": cross_timeframe_indicators,
                "volume_profiles": volume_profiles,
                "market_structures": market_structures,
                "data_source": "trading_service",
                "data_quality": trading_data.get("data_quality", {}),
                "statistics": trading_data.get("statistics", {}),
                "market_overview": trading_data.get("market_overview", {})
            }
            
        except Exception as e:
            logger.error(f"Error collecting technical data for {symbol}: {str(e)}")
            return {"error": str(e)}

    
        """
        从交易所获取真实OHLCV数据
        
        Args:
            symbol: 交易对符号
            start_dt: 开始时间
            end_dt: 结束时间
            
        Returns:
            OHLCV数据列表或None
        """
        try:
            # 导入交易所管理器
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../data_sources'))
            from exchange_data_sources import exchange_manager
            
            # 计算需要的数据点数量
            time_diff = end_dt - start_dt
            hours_needed = time_diff.total_seconds() / 3600
            limit = min(int(hours_needed), 1000)  # CCXT限制
            
            # 尝试从多个交易所获取数据
            exchanges_to_try = ['binance', 'okx', 'huobi']
            
            for exchange_name in exchanges_to_try:
                try:
                    ohlcv_data = exchange_manager.get_ohlcv(
                        symbol=symbol,
                        timeframe='1h',
                        limit=limit,
                        exchange=exchange_name
                    )
                    
                    if ohlcv_data:
                        logger.info(f"成功从 {exchange_name} 获取 {symbol} 数据")
                        return ohlcv_data
                    
                except Exception as e:
                    logger.warning(f"从 {exchange_name} 获取数据失败: {e}")
                    continue
            
            logger.warning(f"无法从任何交易所获取 {symbol} 的数据")
            return None
            
        except Exception as e:
            logger.error(f"获取真实OHLCV数据失败: {e}")
            return None

    
        """
        基于真实数据计算技术指标
        
        Args:
            ohlcv_data: OHLCV数据
            
        Returns:
            技术指标字典
        """
        try:
            if len(ohlcv_data) < 14:  # 最少需要14个数据点计算RSI
                return self._calculate_mock_indicators()
            
            import numpy as np
            
            # 提取价格数据
            closes = [float(candle['close']) for candle in ohlcv_data]
            highs = [float(candle['high']) for candle in ohlcv_data]
            lows = [float(candle['low']) for candle in ohlcv_data]
            volumes = [float(candle['volume']) for candle in ohlcv_data]
            
            indicators = {}
            
            # 计算RSI
            indicators['rsi'] = self._calculate_rsi(closes)
            
            # 计算MACD
            indicators['macd'] = self._calculate_macd(closes)
            
            # 计算布林带
            indicators['bollinger_bands'] = self._calculate_bollinger_bands(closes)
            
            # 计算随机指标
            indicators['stochastic'] = self._calculate_stochastic(highs, lows, closes)
            
            # 计算威廉指标
            indicators['williams_r'] = self._calculate_williams_r(highs, lows, closes)
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算真实技术指标失败: {e}")
            return self._calculate_mock_indicators()

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Dict[str, Any]:
        """计算RSI指标"""
        try:
            if len(prices) < period + 1:
                return {"value": 50.0, "signal": "neutral"}
            
            # 计算价格变化
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # 计算平均增益和损失
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # 生成信号
            if rsi > 70:
                signal = "overbought"
            elif rsi < 30:
                signal = "oversold"
            else:
                signal = "neutral"
            
            return {"value": round(rsi, 2), "signal": signal}
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return {"value": 50.0, "signal": "neutral"}

    def _calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
        """计算MACD指标"""
        try:
            if len(prices) < slow + signal:
                return {"macd": 0.0, "signal": 0.0, "histogram": 0.0, "signal": "neutral"}
            
            # 计算EMA
            def calculate_ema(data, period):
                alpha = 2 / (period + 1)
                ema = [data[0]]
                for i in range(1, len(data)):
                    ema.append(alpha * data[i] + (1 - alpha) * ema[i-1])
                return ema
            
            ema_fast = calculate_ema(prices, fast)
            ema_slow = calculate_ema(prices, slow)
            
            # 计算MACD线
            macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
            
            # 计算信号线
            signal_line = calculate_ema(macd_line, signal)
            
            # 计算直方图
            histogram = [macd_line[i + signal - 1] - signal_line[i] for i in range(len(signal_line))]
            
            # 获取最新值
            macd_value = macd_line[-1]
            signal_value = signal_line[-1]
            histogram_value = histogram[-1]
            
            # 生成信号
            if histogram_value > 0 and macd_value > signal_value:
                signal_type = "bullish"
            elif histogram_value < 0 and macd_value < signal_value:
                signal_type = "bearish"
            else:
                signal_type = "neutral"
            
            return {
                "macd": round(macd_value, 2),
                "signal": round(signal_value, 2),
                "histogram": round(histogram_value, 2),
                "signal": signal_type
            }
            
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0, "signal": "neutral"}

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
        """计算布林带"""
        try:
            if len(prices) < period:
                return {"upper": 0.0, "middle": 0.0, "lower": 0.0, "position": "middle", "signal": "neutral"}
            
            # 计算中轨（SMA）
            middle_band = np.mean(prices[-period:])
            
            # 计算标准差
            std = np.std(prices[-period:])
            
            # 计算上下轨
            upper_band = middle_band + (std_dev * std)
            lower_band = middle_band - (std_dev * std)
            
            # 获取当前价格
            current_price = prices[-1]
            
            # 判断位置
            if current_price >= upper_band:
                position = "upper"
                signal = "overbought"
            elif current_price <= lower_band:
                position = "lower"
                signal = "oversold"
            else:
                position = "middle"
                signal = "neutral"
            
            return {
                "upper": round(upper_band, 2),
                "middle": round(middle_band, 2),
                "lower": round(lower_band, 2),
                "position": position,
                "signal": signal
            }
            
        except Exception as e:
            logger.error(f"计算布林带失败: {e}")
            return {"upper": 0.0, "middle": 0.0, "lower": 0.0, "position": "middle", "signal": "neutral"}

    def _calculate_stochastic(self, highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Dict[str, Any]:
        """计算随机指标"""
        try:
            if len(highs) < k_period + d_period:
                return {"k": 50.0, "d": 50.0, "signal": "neutral"}
            
            # 计算K值
            k_values = []
            for i in range(k_period - 1, len(closes)):
                highest_high = max(highs[i - k_period + 1:i + 1])
                lowest_low = min(lows[i - k_period + 1:i + 1])
                
                if highest_high == lowest_low:
                    k = 50.0
                else:
                    k = 100 * (closes[i] - lowest_low) / (highest_high - lowest_low)
                
                k_values.append(k)
            
            # 计算D值（K值的SMA）
            d_values = []
            for i in range(d_period - 1, len(k_values)):
                d = np.mean(k_values[i - d_period + 1:i + 1])
                d_values.append(d)
            
            k_value = k_values[-1]
            d_value = d_values[-1]
            
            # 生成信号
            if k_value > 80 and d_value > 80:
                signal = "overbought"
            elif k_value < 20 and d_value < 20:
                signal = "oversold"
            else:
                signal = "neutral"
            
            return {
                "k": round(k_value, 2),
                "d": round(d_value, 2),
                "signal": signal
            }
            
        except Exception as e:
            logger.error(f"计算随机指标失败: {e}")
            return {"k": 50.0, "d": 50.0, "signal": "neutral"}

    def _calculate_williams_r(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Dict[str, Any]:
        """计算威廉指标"""
        try:
            if len(highs) < period:
                return {"value": -50.0, "signal": "neutral"}
            
            # 计算威廉%R
            highest_high = max(highs[-period:])
            lowest_low = min(lows[-period:])
            current_close = closes[-1]
            
            if highest_high == lowest_low:
                williams_r = -50.0
            else:
                williams_r = -100 * (highest_high - current_close) / (highest_high - lowest_low)
            
            # 生成信号
            if williams_r > -20:
                signal = "overbought"
            elif williams_r < -80:
                signal = "oversold"
            else:
                signal = "neutral"
            
            return {
                "value": round(williams_r, 2),
                "signal": signal
            }
            
        except Exception as e:
            logger.error(f"计算威廉指标失败: {e}")
            return {"value": -50.0, "signal": "neutral"}
    
    def _analyze_real_volume_profile(self, ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """
        分析真实成交量分布
        
        Args:
            ohlcv_data: OHLCV数据
            
        Returns:
            成交量分析结果
        """
        try:
            if len(ohlcv_data) < 10:
                return self._generate_volume_profile()
            
            volumes = [float(candle['volume']) for candle in ohlcv_data]
            closes = [float(candle['close']) for candle in ohlcv_data]
            
            # 计算成交量趋势
            recent_volume = np.mean(volumes[-5:])
            earlier_volume = np.mean(volumes[-10:-5])
            
            if recent_volume > earlier_volume * 1.2:
                volume_trend = "increasing"
            elif recent_volume < earlier_volume * 0.8:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"
            
            # 计算买卖压力（简化版）
            price_changes = np.diff(closes)
            volume_changes = volumes[1:]
            
            buying_volume = sum(vol for change, vol in zip(price_changes, volume_changes) if change > 0)
            selling_volume = sum(vol for change, vol in zip(price_changes, volume_changes) if change < 0)
            
            total_volume = buying_volume + selling_volume
            buy_pressure = buying_volume / total_volume if total_volume > 0 else 0.5
            sell_pressure = selling_volume / total_volume if total_volume > 0 else 0.5
            
            # 检测成交量峰值
            avg_volume = np.mean(volumes)
            volume_spike = any(v > avg_volume * 2 for v in volumes[-5:])
            
            return {
                "volume_trend": volume_trend,
                "buying_pressure": "high" if buy_pressure > 0.6 else "moderate" if buy_pressure > 0.4 else "low",
                "selling_pressure": "high" if sell_pressure > 0.6 else "moderate" if sell_pressure > 0.4 else "low",
                "volume_spike": volume_spike,
                "accumulation_phase": buy_pressure > sell_pressure,
                "avg_volume": round(avg_volume, 2),
                "current_volume": round(volumes[-1], 2),
            }
            
        except Exception as e:
            logger.error(f"分析成交量分布失败: {e}")
            return self._generate_volume_profile()
    
    def _analyze_real_market_structure(self, ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """
        分析真实市场结构
        
        Args:
            ohlcv_data: OHLCV数据
            
        Returns:
            市场结构分析结果
        """
        try:
            if len(ohlcv_data) < 20:
                return self._analyze_market_structure()
            
            highs = [float(candle['high']) for candle in ohlcv_data]
            lows = [float(candle['low']) for candle in ohlcv_data]
            closes = [float(candle['close']) for candle in ohlcv_data]
            
            # 识别更高的高点和更高的低点
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            higher_highs = recent_highs[-1] > recent_highs[0]
            higher_lows = recent_lows[-1] > recent_lows[0]
            
            # 判断趋势
            if higher_highs and higher_lows:
                trend = "uptrend"
            elif not higher_highs and not higher_lows:
                trend = "downtrend"
            else:
                trend = "sideways"
            
            # 简化的形态识别
            price_range = max(highs[-20:]) - min(lows[-20:])
            current_price = closes[-1]
            position_in_range = (current_price - min(lows[-20:])) / price_range
            
            if position_in_range > 0.8:
                pattern = "resistance_test"
            elif position_in_range < 0.2:
                pattern = "support_test"
            elif 0.4 <= position_in_range <= 0.6:
                pattern = "consolidation"
            else:
                pattern = "undefined"
            
            # 突破潜力
            volatility = np.std(closes[-10:]) / np.mean(closes[-10:])
            breakout_potential = "high" if volatility > 0.03 else "medium" if volatility > 0.01 else "low"
            
            return {
                "higher_highs": higher_highs,
                "higher_lows": higher_lows,
                "trend": trend,
                "pattern": pattern,
                "breakout_potential": breakout_potential,
                "price_range": round(price_range, 2),
                "position_in_range": round(position_in_range, 2),
                "volatility": round(volatility, 4),
            }
            
        except Exception as e:
            logger.error(f"分析市场结构失败: {e}")
            return self._analyze_market_structure()
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析技术数据 - 增强版本支持AI分析
        
        Args:
            data: 技术分析数据
            
        Returns:
            技术分析结果（包含AI增强分析）
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            indicators = data.get("indicators", {})
            market_structure = data.get("market_structure", {})
            
            # 执行传统技术分析
            traditional_analysis = self._perform_traditional_analysis(data, indicators, market_structure)
            
            # 如果启用了AI增强分析，则进行AI分析
            if self.ai_analyzer and self.ai_analyzer.ai_enabled:
                try:
                    logger.info("开始AI增强技术分析")
                    ai_enhanced_analysis = self.ai_analyzer.analyze_with_ai(traditional_analysis, data)
                    
                    # 返回增强后的分析结果
                    return {
                        **traditional_analysis,
                        "ai_enhanced": True,
                        "ai_analysis": ai_enhanced_analysis.get("ai_analysis", {}),
                        "combined_insights": ai_enhanced_analysis.get("combined_insights", {}),
                        "final_recommendation": ai_enhanced_analysis.get("final_recommendation", {}),
                        "enhanced_insights": ai_enhanced_analysis.get("enhanced_insights", {}),
                        "analysis_type": "ai_enhanced"
                    }
                    
                except Exception as ai_error:
                    logger.error(f"AI增强分析失败: {ai_error}")
                    # AI失败时返回传统分析结果
                    return {
                        **traditional_analysis,
                        "ai_enhanced": False,
                        "ai_error": str(ai_error),
                        "analysis_type": "traditional_only"
                    }
            else:
                # 只进行传统分析
                return {
                    **traditional_analysis,
                    "ai_enhanced": False,
                    "analysis_type": "traditional_only"
                }
            
        except Exception as e:
            logger.error(f"Error analyzing technical data: {str(e)}")
            return {"error": str(e)}

    async def run(self, symbol: str = "BTC/USDT", timeframe: str = "1d") -> Dict[str, Any]:
        """
        统一对外接口函数，执行完整的技术分析流程
        
        Args:
            symbol: 交易对符号，如 'BTC/USDT'
            timeframe: 时间周期，如 '1d', '4h', '1h'
            
        Returns:
            Dict[str, Any]: 完整的分析结果
        """
        try:
            # 步骤1：收集数据
            collected_data = await self.collect_data(symbol, timeframe)
            
            # 步骤2：执行分析
            analysis_result = await self.analyze(collected_data)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"TechnicalAnalyst run失败: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'symbol': symbol,
                'timeframe': timeframe,
                'analysis_type': 'technical'
            }
    
    def _perform_traditional_analysis(self, data: Dict[str, Any], indicators: Dict[str, Any], 
                                    market_structure: Dict[str, Any]) -> Dict[str, Any]:
        """执行传统技术分析"""
        # 计算技术信号
        signals = self._calculate_technical_signals(indicators)
        
        # 计算趋势强度
        trend_strength = self._calculate_trend_strength(indicators, market_structure)
        
        # 计算支撑阻力位
        support_resistance = self._calculate_support_resistance(data)
        
        # 计算波动率
        volatility = self._calculate_volatility(data)
        
        # 风险评估
        risk_assessment = self._assess_technical_risk(signals, volatility)
        
        return {
            "indicators": indicators,
            "signals": signals,
            "trend_strength": trend_strength,
            "support_resistance": support_resistance,
            "volatility": volatility,
            "risk_indicators": risk_assessment,
            "market_regime": self._determine_market_regime(signals, trend_strength),
            "confidence": self._calculate_confidence(signals, trend_strength),
            "key_observations": self._generate_key_observations(signals, market_structure),
        }
    
    
        """生成模拟OHLCV数据"""
        # TODO: 替换为真实数据源
        mock_data = []
        base_price = 50000 if "BTC" in symbol else 3000  # 模拟基础价格
        
        current_time = start_dt
        while current_time <= end_dt:
            # 添加随机波动
            random_change = (hash(str(current_time)) % 1000 - 500) / 10000
            price = base_price * (1 + random_change)
            
            mock_data.append({
                "timestamp": current_time.isoformat(),
                "open": price * 0.999,
                "high": price * 1.005,
                "low": price * 0.995,
                "close": price,
                "volume": hash(str(current_time)) % 1000000 + 100000,
            })
            
            current_time += timedelta(hours=1)
        
        return mock_data
    
    
        """计算模拟技术指标"""
        return {
            "rsi": {"value": 65.5, "signal": "neutral"},
            "macd": {"macd": 125.3, "signal": 98.7, "histogram": 26.6, "signal": "bullish"},
            "bollinger_bands": {
                "upper": 52000,
                "middle": 50000,
                "lower": 48000,
                "position": "middle",
                "signal": "neutral"
            },
            "ichimoku": {
                "tenkan_sen": 50200,
                "kijun_sen": 49800,
                "senkou_span_a": 50100,
                "senkou_span_b": 49900,
                "chikou_span": 50300,
                "signal": "bullish"
            },
            "stochastic": {"k": 75.2, "d": 68.9, "signal": "overbought"},
            "williams_r": {"value": -25.3, "signal": "neutral"},
        }
    
    
        """生成成交量分布"""
        return {
            "volume_trend": "increasing",
            "buying_pressure": "moderate",
            "selling_pressure": "low",
            "volume_spike": False,
            "accumulation_phase": True,
        }
    
    def _analyze_market_structure(self) -> Dict[str, Any]:
        """分析市场结构"""
        return {
            "higher_highs": True,
            "higher_lows": True,
            "trend": "uptrend",
            "pattern": "ascending_triangle",
            "breakout_potential": "high",
        }
    
    
        """获取分层数据"""
        try:
            layered_data = self.exchange_manager.get_layered_ohlcv_30d(symbol)
            return layered_data
        except Exception as e:
            logger.error(f"获取分层数据失败: {e}")
            return {}
    
    
        """计算分层技术指标"""
        indicators = {}
        
        for layer_name, layer_info in layered_data.get("layers", {}).items():
            ohlcv_data = layer_info.get("data", [])
            if not ohlcv_data:
                continue
                
            # 计算各层的基本指标
            layer_indicators = self._calculate_basic_indicators(ohlcv_data)
            indicators[layer_name] = layer_indicators
        
        # 计算跨层综合指标
        indicators["cross_layer"] = self._calculate_cross_layer_indicators(layered_data)
        
        return indicators
    
    def _calculate_basic_indicators(self, ohlcv_data: List) -> Dict[str, Any]:
        """计算基本技术指标"""
        if not ohlcv_data:
            return {}
        
        # 适配不同的数据格式
        if isinstance(ohlcv_data[0], dict):
            # 字典格式数据
            closes = [float(candle['close']) for candle in ohlcv_data]
            highs = [float(candle['high']) for candle in ohlcv_data]
            lows = [float(candle['low']) for candle in ohlcv_data]
            volumes = [float(candle['volume']) for candle in ohlcv_data]
        else:
            # 列表格式数据
            closes = [float(candle[4]) for candle in ohlcv_data]
            highs = [float(candle[2]) for candle in ohlcv_data]
            lows = [float(candle[3]) for candle in ohlcv_data]
            volumes = [float(candle[5]) for candle in ohlcv_data]
        
        indicators = {}
        
        # 移动平均线
        if len(closes) >= 20:
            indicators["sma_20"] = sum(closes[-20:]) / 20
        if len(closes) >= 50:
            indicators["sma_50"] = sum(closes[-50:]) / 50
        if len(closes) >= 200:
            indicators["sma_200"] = sum(closes[-200:]) / 200
        
        # 指数移动平均线
        if len(closes) >= 12:
            indicators["ema_12"] = self._calculate_ema(closes, 12)
        if len(closes) >= 26:
            indicators["ema_26"] = self._calculate_ema(closes, 26)
        
        # RSI
        if len(closes) >= 14:
            indicators["rsi"] = self._calculate_rsi(closes)
        
        # MACD
        if len(closes) >= 26:
            macd_data = self._calculate_macd_enhanced(closes)
            indicators.update(macd_data)
        
        # 布林带
        if len(closes) >= 20:
            bb_data = self._calculate_bollinger_bands_enhanced(closes)
            indicators.update(bb_data)
        
        # 成交量指标
        if volumes:
            indicators["volume_avg"] = sum(volumes) / len(volumes)
            indicators["volume_trend"] = self._calculate_volume_trend(volumes)
        
        # 价格变化
        if len(closes) > 1:
            price_change = (closes[-1] - closes[0]) / closes[0] * 100
            indicators["price_change"] = price_change
            
            # 波动率
            if len(closes) >= 20:
                returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                volatility = (sum(r*r for r in returns) / len(returns)) ** 0.5
                indicators["volatility"] = volatility
        
        return indicators
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """计算指数移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def _calculate_macd_enhanced(self, prices: List[float]) -> Dict[str, float]:
        """计算增强MACD指标"""
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        signal_line = self._calculate_ema([macd_line] * min(9, len(prices)), 9)
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": histogram
        }
    
    def _calculate_bollinger_bands_enhanced(self, prices: List[float]) -> Dict[str, float]:
        """计算增强布林带指标"""
        if len(prices) < 20:
            return {}
        
        sma_20 = sum(prices[-20:]) / 20
        std = (sum((p - sma_20) ** 2 for p in prices[-20:]) / 20) ** 0.5
        
        upper_band = sma_20 + (2 * std)
        lower_band = sma_20 - (2 * std)
        
        # 计算带宽
        bandwidth = (upper_band - lower_band) / sma_20
        
        # 计算%B指标
        current_price = prices[-1]
        if upper_band != lower_band:
            percent_b = (current_price - lower_band) / (upper_band - lower_band)
        else:
            percent_b = 0.5
        
        return {
            "bb_upper": upper_band,
            "bb_middle": sma_20,
            "bb_lower": lower_band,
            "bb_bandwidth": bandwidth,
            "bb_percent_b": percent_b
        }
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """计算RSI指标"""
        if len(closes) < period + 1:
            return 50.0
            
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [delta for delta in deltas if delta > 0]
        losses = [abs(delta) for delta in deltas if delta < 0]
        
        avg_gain = sum(gains[-period:]) / period if len(gains) >= period else (sum(gains) / len(gains) if gains else 0)
        avg_loss = sum(losses[-period:]) / period if len(losses) >= period else (sum(losses) / len(losses) if losses else 0)
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_cross_layer_indicators(self, layered_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算跨层综合指标"""
        layers = layered_data.get("layers", {})
        
        # 获取各层的收盘价
        layer_closes = {}
        for layer_name, layer_info in layers.items():
            ohlcv_data = layer_info.get("data", [])
            if ohlcv_data:
                layer_closes[layer_name] = [float(candle[4]) for candle in ohlcv_data]
        
        if not layer_closes:
            return {}
        
        # 计算趋势一致性
        trend_consistency = self._calculate_trend_consistency(layer_closes)
        
        # 计算波动率递减
        volatility_decay = self._calculate_volatility_decay(layer_closes)
        
        return {
            "trend_consistency": trend_consistency,
            "volatility_decay": volatility_decay,
            "multi_timeframe_signal": self._generate_multi_timeframe_signal(layer_closes)
        }
    
    def _calculate_trend_consistency(self, layer_closes: Dict[str, List[float]]) -> float:
        """计算趋势一致性"""
        if len(layer_closes) < 2:
            return 0.0
        
        trends = []
        for closes in layer_closes.values():
            if len(closes) >= 2:
                trend = 1 if closes[-1] > closes[0] else -1
                trends.append(trend)
        
        if not trends:
            return 0.0
        
        consistency = sum(trends) / len(trends)
        return abs(consistency)
    
    def _calculate_volatility_decay(self, layer_closes: Dict[str, List[float]]) -> float:
        """计算波动率递减"""
        volatilities = []
        
        for closes in layer_closes.values():
            if len(closes) >= 10:
                returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                volatility = sum(r**2 for r in returns) / len(returns)
                volatilities.append(volatility)
        
        if len(volatilities) < 2:
            return 0.0
        
        # 计算波动率递减率
        volatility_ratio = volatilities[-1] / volatilities[0] if volatilities[0] != 0 else 1.0
        return 1.0 - volatility_ratio
    
    def _generate_multi_timeframe_signal(self, layer_closes: Dict[str, List[float]]) -> str:
        """生成多时间框架信号"""
        signals = []
        
        for closes in layer_closes.values():
            if len(closes) >= 20:
                sma_20 = sum(closes[-20:]) / 20
                current_price = closes[-1]
                
                if current_price > sma_20:
                    signals.append("bullish")
                else:
                    signals.append("bearish")
        
        if not signals:
            return "neutral"
        
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")
        
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"
    
    
        """分析分层成交量分布"""
        volume_analysis = {}
        
        for layer_name, layer_info in layered_data.get("layers", {}).items():
            ohlcv_data = layer_info.get("data", [])
            if not ohlcv_data:
                continue
                
            volumes = [float(candle[5]) for candle in ohlcv_data]
            
            # 计算成交量指标
            volume_analysis[layer_name] = {
                "volume_avg": sum(volumes) / len(volumes) if volumes else 0,
                "volume_trend": self._calculate_volume_trend(volumes),
                "volume_spike": self._detect_volume_spike(volumes),
                "accumulation_index": self._calculate_accumulation_index(ohlcv_data)
            }
        
        # 跨层成交量分析
        volume_analysis["cross_layer"] = self._analyze_cross_layer_volume(layered_data)
        
        return volume_analysis
    
    def _calculate_volume_trend(self, volumes: List[float]) -> str:
        """计算成交量趋势"""
        if len(volumes) < 10:
            return "neutral"
        
        recent_avg = sum(volumes[-5:]) / 5
        earlier_avg = sum(volumes[-10:-5]) / 5
        
        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        elif recent_avg < earlier_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _detect_volume_spike(self, volumes: List[float]) -> bool:
        """检测成交量异常"""
        if len(volumes) < 20:
            return False
        
        recent_volume = volumes[-1]
        avg_volume = sum(volumes[-20:]) / 20
        
        return recent_volume > avg_volume * 2.0
    
    def _calculate_accumulation_index(self, ohlcv_data: List) -> float:
        """计算积累指数"""
        if len(ohlcv_data) < 10:
            return 0.0
        
        closes = [float(candle[4]) for candle in ohlcv_data]
        volumes = [float(candle[5]) for candle in ohlcv_data]
        
        # 计算价格变动与成交量的相关性
        price_changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        volume_changes = [volumes[i] - volumes[i-1] for i in range(1, len(volumes))]
        
        if len(price_changes) != len(volume_changes):
            return 0.0
        
        # 简单的相关性计算
        correlation = 0.0
        for i in range(len(price_changes)):
            if price_changes[i] * volume_changes[i] > 0:
                correlation += 1
        
        return correlation / len(price_changes) if price_changes else 0.0
    
    def _analyze_cross_layer_volume(self, layered_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析跨层成交量"""
        layers = layered_data.get("layers", {})
        
        volume_ratios = []
        volume_patterns = []
        
        for layer_name, layer_info in layers.items():
            ohlcv_data = layer_info.get("data", [])
            if ohlcv_data:
                volumes = [float(candle[5]) for candle in ohlcv_data]
                volume_ratios.append(sum(volumes))
                volume_patterns.append(self._calculate_volume_trend(volumes))
        
        return {
            "volume_distribution": "balanced" if len(set(volume_patterns)) == 1 else "divergent",
            "liquidity_score": sum(volume_ratios) / len(volume_ratios) if volume_ratios else 0,
            "volume_consistency": volume_patterns.count("stable") / len(volume_patterns) if volume_patterns else 0
        }
    
    
        """分析分层市场结构"""
        structure_analysis = {}
        
        for layer_name, layer_info in layered_data.get("layers", {}).items():
            ohlcv_data = layer_info.get("data", [])
            if not ohlcv_data:
                continue
                
            highs = [float(candle[2]) for candle in ohlcv_data]
            lows = [float(candle[3]) for candle in ohlcv_data]
            closes = [float(candle[4]) for candle in ohlcv_data]
            
            structure_analysis[layer_name] = {
                "higher_highs": self._detect_higher_highs(highs),
                "higher_lows": self._detect_higher_lows(lows),
                "trend": self._determine_trend(closes),
                "support_resistance": self._find_support_resistance(highs, lows)
            }
        
        # 跨层市场结构分析
        structure_analysis["cross_layer"] = self._analyze_cross_layer_structure(layered_data)
        
        return structure_analysis
    
    def _detect_higher_highs(self, highs: List[float]) -> bool:
        """检测更高的高点"""
        if len(highs) < 5:
            return False
        
        recent_highs = highs[-5:]
        return recent_highs[-1] > recent_highs[0]
    
    def _detect_higher_lows(self, lows: List[float]) -> bool:
        """检测更高的低点"""
        if len(lows) < 5:
            return False
        
        recent_lows = lows[-5:]
        return recent_lows[-1] > recent_lows[0]
    
    def _determine_trend(self, closes: List[float]) -> str:
        """确定趋势"""
        if len(closes) < 20:
            return "neutral"
        
        sma_20 = sum(closes[-20:]) / 20
        current_price = closes[-1]
        
        if current_price > sma_20 * 1.02:
            return "uptrend"
        elif current_price < sma_20 * 0.98:
            return "downtrend"
        else:
            return "neutral"
    
    def _find_support_resistance(self, highs: List[float], lows: List[float]) -> Dict[str, float]:
        """寻找支撑阻力位"""
        if not highs or not lows:
            return {"support": 0, "resistance": 0}
        
        resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        
        return {"support": support, "resistance": resistance}
    
    def _analyze_cross_layer_structure(self, layered_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析跨层市场结构"""
        layers = layered_data.get("layers", {})
        
        trends = []
        signals = []
        
        for layer_name, layer_info in layers.items():
            ohlcv_data = layer_info.get("data", [])
            if ohlcv_data:
                closes = [float(candle[4]) for candle in ohlcv_data]
                trend = self._determine_trend(closes)
                trends.append(trend)
                
                # 生成层信号
                signal = self._generate_layer_signal(closes)
                signals.append(signal)
        
        return {
            "trend_alignment": trends.count(trends[0]) / len(trends) if trends else 0,
            "market_regime": self._determine_market_regime(trends),
            "confidence_score": sum(1 for s in signals if s == "strong") / len(signals) if signals else 0
        }
    
    def _generate_layer_signal(self, closes: List[float]) -> str:
        """生成层信号"""
        if len(closes) < 20:
            return "weak"
        
        sma_20 = sum(closes[-20:]) / 20
        current_price = closes[-1]
        
        # 简单的信号强度评估
        deviation = abs(current_price - sma_20) / sma_20
        
        if deviation > 0.05:
            return "strong"
        elif deviation > 0.02:
            return "moderate"
        else:
            return "weak"
    
    def _determine_market_regime(self, trends: List[str]) -> str:
        """确定市场状态"""
        if not trends:
            return "unknown"
        
        uptrend_count = trends.count("uptrend")
        downtrend_count = trends.count("downtrend")
        
        if uptrend_count > downtrend_count:
            return "bullish"
        elif downtrend_count > uptrend_count:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_technical_signals(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """计算技术信号"""
        signals = {
            "bullish_signals": [],
            "bearish_signals": [],
            "neutral_signals": [],
        }
        
        # RSI信号
        rsi = indicators.get("rsi", {}).get("value", 50)
        if rsi > 70:
            signals["bearish_signals"].append("RSI超买")
        elif rsi < 30:
            signals["bullish_signals"].append("RSI超卖")
        
        # MACD信号
        macd_signal = indicators.get("macd", {}).get("signal", "neutral")
        if macd_signal == "bullish":
            signals["bullish_signals"].append("MACD金叉")
        elif macd_signal == "bearish":
            signals["bearish_signals"].append("MACD死叉")
        
        # 布林带信号
        bb_position = indicators.get("bollinger_bands", {}).get("position", "middle")
        if bb_position == "upper":
            signals["bearish_signals"].append("价格接近布林带上轨")
        elif bb_position == "lower":
            signals["bullish_signals"].append("价格接近布林带下轨")
        
        return signals
    
    def _calculate_trend_strength(self, indicators: Dict[str, Any], market_structure: Dict[str, Any]) -> Dict[str, Any]:
        """计算趋势强度"""
        ichimoku = indicators.get("ichimoku", {})
        structure = market_structure
        
        # 基于多个因素计算趋势强度
        trend_factors = []
        
        # Ichimoku信号
        if ichimoku.get("signal") == "bullish":
            trend_factors.append(0.7)
        elif ichimoku.get("signal") == "bearish":
            trend_factors.append(-0.7)
        
        # 市场结构
        if structure.get("trend") == "uptrend":
            trend_factors.append(0.6)
        elif structure.get("trend") == "downtrend":
            trend_factors.append(-0.6)
        
        # 计算平均趋势强度
        if trend_factors:
            avg_strength = sum(trend_factors) / len(trend_factors)
        else:
            avg_strength = 0.0
        
        return {
            "strength": abs(avg_strength),
            "direction": "bullish" if avg_strength > 0 else "bearish" if avg_strength < 0 else "neutral",
            "confidence": min(abs(avg_strength) * 1.5, 1.0),
        }
    
    def _calculate_support_resistance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算支撑阻力位"""
        ohlcv = data.get("ohlcv_data", [])
        
        if not ohlcv:
            return {"support": [], "resistance": []}
        
        # 简化的支撑阻力计算
        prices = [candle["close"] for candle in ohlcv[-50:]]  # 最近50个价格
        
        support_level = min(prices) * 0.98
        resistance_level = max(prices) * 1.02
        
        return {
            "support": [support_level],
            "resistance": [resistance_level],
            "key_levels": [support_level, resistance_level],
            "breakout_points": resistance_level * 1.01,
        }
    
    def _calculate_volatility(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算波动率"""
        ohlcv = data.get("ohlcv_data", [])
        
        if len(ohlcv) < 2:
            return {"volatility": 0.0, "atr": 0.0}
        
        # 计算价格变化
        prices = [candle["close"] for candle in ohlcv[-20:]]
        
        if len(prices) < 2:
            return {"volatility": 0.0, "atr": 0.0}
        
        # 计算标准差波动率
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum(r*r for r in returns) / len(returns)) ** 0.5
        
        # 简化的ATR计算
        atr = sum(abs(prices[i] - prices[i-1]) for i in range(1, len(prices))) / len(prices)
        
        return {
            "volatility": volatility,
            "atr": atr,
            "volatility_regime": "high" if volatility > 0.05 else "low" if volatility < 0.02 else "normal",
        }
    
    def _assess_technical_risk(self, signals: Dict[str, Any], volatility: Dict[str, Any]) -> Dict[str, Any]:
        """评估技术风险"""
        risk_score = 0.0
        risk_factors = []
        
        # 基于信号数量评估风险
        total_signals = len(signals["bullish_signals"]) + len(signals["bearish_signals"])
        if total_signals == 0:
            risk_score += 0.3
            risk_factors.append("信号不足")
        
        # 基于波动率评估风险
        vol_level = volatility.get("volatility_regime", "normal")
        if vol_level == "high":
            risk_score += 0.4
            risk_factors.append("高波动率")
        elif vol_level == "low":
            risk_score += 0.1
            risk_factors.append("低波动率")
        
        return {
            "overall_score": min(risk_score, 1.0),
            "key_risks": risk_factors,
            "risk_level": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
        }
    
    def _determine_market_regime(self, signals: Dict[str, Any], trend_strength: Dict[str, Any]) -> str:
        """确定市场状态"""
        bullish_count = len(signals["bullish_signals"])
        bearish_count = len(signals["bearish_signals"])
        trend_dir = trend_strength.get("direction", "neutral")
        
        if bullish_count > bearish_count and trend_dir == "bullish":
            return "strong_uptrend"
        elif bearish_count > bullish_count and trend_dir == "bearish":
            return "strong_downtrend"
        elif bullish_count == bearish_count:
            return "ranging"
        else:
            return "weak_trend"
    
    def _calculate_confidence(self, signals: Dict[str, Any], trend_strength: Dict[str, Any]) -> float:
        """计算分析置信度"""
        # 基于信号一致性和趋势强度计算置信度
        total_signals = len(signals["bullish_signals"]) + len(signals["bearish_signals"])
        signal_consistency = abs(len(signals["bullish_signals"]) - len(signals["bearish_signals"])) / max(total_signals, 1)
        
        trend_confidence = trend_strength.get("confidence", 0.5)
        
        return (signal_consistency + trend_confidence) / 2
    
    def _calculate_timeframe_indicators(self, ohlcv_data: List) -> Dict[str, Any]:
        """计算单个时间周期的技术指标"""
        if not ohlcv_data:
            return {}
        
        # 适配不同的数据格式
        if isinstance(ohlcv_data[0], dict):
            # 字典格式数据
            closes = [float(candle['close']) for candle in ohlcv_data]
            highs = [float(candle['high']) for candle in ohlcv_data]
            lows = [float(candle['low']) for candle in ohlcv_data]
            volumes = [float(candle['volume']) for candle in ohlcv_data]
        else:
            # 列表格式数据
            closes = [float(candle[4]) for candle in ohlcv_data]
            highs = [float(candle[2]) for candle in ohlcv_data]
            lows = [float(candle[3]) for candle in ohlcv_data]
            volumes = [float(candle[5]) for candle in ohlcv_data]
        
        indicators = {}
        
        # 移动平均线
        if len(closes) >= 20:
            indicators["sma_20"] = sum(closes[-20:]) / 20
        if len(closes) >= 50:
            indicators["sma_50"] = sum(closes[-50:]) / 50
        if len(closes) >= 200:
            indicators["sma_200"] = sum(closes[-200:]) / 200
        
        # 指数移动平均线
        if len(closes) >= 12:
            indicators["ema_12"] = self._calculate_ema(closes, 12)
        if len(closes) >= 26:
            indicators["ema_26"] = self._calculate_ema(closes, 26)
        
        # RSI
        if len(closes) >= 14:
            indicators["rsi"] = self._calculate_rsi(closes)
        
        # MACD
        if len(closes) >= 26:
            macd_data = self._calculate_macd_enhanced(closes)
            indicators.update(macd_data)
        
        # 布林带
        if len(closes) >= 20:
            bb_data = self._calculate_bollinger_bands_enhanced(closes)
            indicators.update(bb_data)
        
        # 成交量指标
        if volumes:
            indicators["volume_avg"] = sum(volumes) / len(volumes)
            indicators["volume_trend"] = self._calculate_volume_trend(volumes)
        
        # 价格变化
        if len(closes) > 1:
            price_change = (closes[-1] - closes[0]) / closes[0] * 100
            indicators["price_change"] = price_change
            
            # 波动率
            if len(closes) >= 20:
                returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                volatility = (sum(r*r for r in returns) / len(returns)) ** 0.5
                indicators["volatility"] = volatility
        
        return indicators
    
    def _analyze_timeframe_volume_profile(self, ohlcv_data: List) -> Dict[str, Any]:
        """分析单个时间周期的成交量分布"""
        if not ohlcv_data:
            return {}
        
        # 提取成交量数据
        if isinstance(ohlcv_data[0], dict):
            volumes = [float(candle['volume']) for candle in ohlcv_data]
            closes = [float(candle['close']) for candle in ohlcv_data]
        else:
            volumes = [float(candle[5]) for candle in ohlcv_data]
            closes = [float(candle[4]) for candle in ohlcv_data]
        
        if not volumes:
            return {}
        
        # 计算成交量趋势
        recent_volume = np.mean(volumes[-5:]) if len(volumes) >= 5 else np.mean(volumes)
        earlier_volume = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else recent_volume
        
        if recent_volume > earlier_volume * 1.2:
            volume_trend = "increasing"
        elif recent_volume < earlier_volume * 0.8:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"
        
        # 计算买卖压力（简化版）
        if len(closes) > 1 and len(volumes) > 1:
            price_changes = np.diff(closes)
            volume_changes = volumes[1:]
            
            buying_volume = sum(vol for change, vol in zip(price_changes, volume_changes) if change > 0)
            selling_volume = sum(vol for change, vol in zip(price_changes, volume_changes) if change < 0)
            
            total_volume = buying_volume + selling_volume
            buy_pressure = buying_volume / total_volume if total_volume > 0 else 0.5
            sell_pressure = selling_volume / total_volume if total_volume > 0 else 0.5
        else:
            buy_pressure = 0.5
            sell_pressure = 0.5
        
        # 检测成交量峰值
        avg_volume = np.mean(volumes)
        volume_spike = any(v > avg_volume * 2 for v in volumes[-5:])
        
        return {
            "volume_trend": volume_trend,
            "buying_pressure": "high" if buy_pressure > 0.6 else "moderate" if buy_pressure > 0.4 else "low",
            "selling_pressure": "high" if sell_pressure > 0.6 else "moderate" if sell_pressure > 0.4 else "low",
            "volume_spike": volume_spike,
            "accumulation_phase": buy_pressure > sell_pressure,
            "avg_volume": round(avg_volume, 2),
            "current_volume": round(volumes[-1], 2),
        }
    
    def _analyze_timeframe_market_structure(self, ohlcv_data: List) -> Dict[str, Any]:
        """分析单个时间周期的市场结构"""
        if not ohlcv_data:
            return {}
        
        # 提取价格数据
        if isinstance(ohlcv_data[0], dict):
            highs = [float(candle['high']) for candle in ohlcv_data]
            lows = [float(candle['low']) for candle in ohlcv_data]
            closes = [float(candle['close']) for candle in ohlcv_data]
        else:
            highs = [float(candle[2]) for candle in ohlcv_data]
            lows = [float(candle[3]) for candle in ohlcv_data]
            closes = [float(candle[4]) for candle in ohlcv_data]
        
        if len(highs) < 20 or len(lows) < 20 or len(closes) < 20:
            return {}
        
        # 识别更高的高点和更高的低点
        recent_highs = highs[-10:]
        recent_lows = lows[-10:]
        
        higher_highs = recent_highs[-1] > recent_highs[0]
        higher_lows = recent_lows[-1] > recent_lows[0]
        
        # 判断趋势
        if higher_highs and higher_lows:
            trend = "uptrend"
        elif not higher_highs and not higher_lows:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        # 简化的形态识别
        price_range = max(highs[-20:]) - min(lows[-20:])
        current_price = closes[-1]
        position_in_range = (current_price - min(lows[-20:])) / price_range
        
        if position_in_range > 0.8:
            pattern = "resistance_test"
        elif position_in_range < 0.2:
            pattern = "support_test"
        elif 0.4 <= position_in_range <= 0.6:
            pattern = "consolidation"
        else:
            pattern = "undefined"
        
        # 突破潜力
        volatility = np.std(closes[-10:]) / np.mean(closes[-10:])
        breakout_potential = "high" if volatility > 0.03 else "medium" if volatility > 0.01 else "low"
        
        return {
            "higher_highs": higher_highs,
            "higher_lows": higher_lows,
            "trend": trend,
            "pattern": pattern,
            "breakout_potential": breakout_potential,
            "price_range": round(price_range, 2),
            "position_in_range": round(position_in_range, 2),
            "volatility": round(volatility, 4),
        }
    
    def _calculate_cross_timeframe_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """计算跨时间周期综合指标"""
        try:
            if not indicators:
                return {}
            
            # 获取各层的收盘价相关数据
            timeframe_closes = {}
            for timeframe_name, timeframe_indicators in indicators.items():
                if "price_change" in timeframe_indicators:
                    timeframe_closes[timeframe_name] = timeframe_indicators
            
            if not timeframe_closes:
                return {}
            
            # 计算趋势一致性
            trend_consistency = self._calculate_trend_consistency(timeframe_closes)
            
            # 计算波动率递减
            volatility_decay = self._calculate_volatility_decay(indicators)
            
            # 计算多时间框架信号
            multi_timeframe_signal = self._generate_multi_timeframe_signal(indicators)
            
            return {
                "trend_consistency": trend_consistency,
                "volatility_decay": volatility_decay,
                "multi_timeframe_signal": multi_timeframe_signal,
                "indicator_alignment": self._calculate_indicator_alignment(indicators)
            }
            
        except Exception as e:
            logger.error(f"计算跨时间周期指标失败: {e}")
            return {}
    
    def _calculate_trend_consistency(self, timeframe_data: Dict[str, Any]) -> float:
        """计算趋势一致性"""
        if len(timeframe_data) < 2:
            return 0.0
        
        trends = []
        for data in timeframe_data.values():
            price_change = data.get("price_change", 0)
            if price_change > 1.0:
                trends.append(1)  # 上涨
            elif price_change < -1.0:
                trends.append(-1)  # 下跌
            else:
                trends.append(0)  # 盘整
        
        if not trends:
            return 0.0
        
        consistency = sum(trends) / len(trends)
        return abs(consistency)
    
    def _calculate_volatility_decay(self, indicators: Dict[str, Any]) -> float:
        """计算波动率递减"""
        volatilities = []
        
        for timeframe_indicators in indicators.values():
            volatility = timeframe_indicators.get("volatility", 0)
            if volatility > 0:
                volatilities.append(volatility)
        
        if len(volatilities) < 2:
            return 0.0
        
        # 计算波动率递减率
        volatility_ratio = volatilities[-1] / volatilities[0] if volatilities[0] != 0 else 1.0
        return 1.0 - volatility_ratio
    
    def _generate_multi_timeframe_signal(self, indicators: Dict[str, Any]) -> str:
        """生成多时间框架信号"""
        signals = []
        
        for timeframe_name, timeframe_indicators in indicators.items():
            if len(timeframe_indicators) >= 20:
                sma_20 = timeframe_indicators.get("sma_20", 0)
                current_price = timeframe_indicators.get("price_change", 0)
                
                # 简化的信号判断
                if current_price > 2.0:  # 2%以上涨幅
                    signals.append("bullish")
                elif current_price < -2.0:  # 2%以上跌幅
                    signals.append("bearish")
                else:
                    signals.append("neutral")
        
        if not signals:
            return "neutral"
        
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")
        
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_indicator_alignment(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """计算指标对齐度"""
        try:
            alignment_scores = {}
            
            for indicator_name in ["rsi", "macd", "sma_20"]:
                values = []
                for timeframe_indicators in indicators.values():
                    if indicator_name in timeframe_indicators:
                        values.append(timeframe_indicators[indicator_name])
                
                if values:
                    # 计算变异系数来衡量一致性
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    cv = std_val / mean_val if mean_val != 0 else 1.0
                    
                    alignment_scores[indicator_name] = {
                        "consistency": 1.0 - min(cv, 1.0),
                        "mean_value": mean_val,
                        "std_value": std_val
                    }
            
            return alignment_scores
            
        except Exception as e:
            logger.error(f"计算指标对齐度失败: {e}")
            return {}

    def _generate_key_observations(self, signals: Dict[str, Any], market_structure: Dict[str, Any]) -> List[str]:
        """生成关键观察"""
        observations = []
        
        # 基于信号的观察
        if signals["bullish_signals"]:
            observations.append(f"看涨信号: {', '.join(signals['bullish_signals'][:2])}")
        if signals["bearish_signals"]:
            observations.append(f"看跌信号: {', '.join(signals['bearish_signals'][:2])}")
        
        # 基于市场结构的观察
        trend = market_structure.get("trend", "unknown")
        observations.append(f"市场趋势: {trend}")
        
        pattern = market_structure.get("pattern", "unknown")
        if pattern != "unknown":
            observations.append(f"图表形态: {pattern}")
        
        return observations
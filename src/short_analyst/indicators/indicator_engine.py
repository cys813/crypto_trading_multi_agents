"""
做空技术指标引擎模块
专门针对做空信号优化的技术指标计算引擎

核心功能：
1. 做空专用指标集合
2. 趋势反转指标
3. 超买指标
4. 压力位指标
5. 成交量指标
6. 市场情绪指标
7. 指标缓存和性能优化
"""

import asyncio
import math
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import logging
from abc import ABC, abstractmethod

# 尝试导入talib，如果不可用则使用模拟版本
try:
    import talib
except ImportError:
    import sys
    import random

    # 创建模拟的talib模块
    class MockTALib:
        @staticmethod
        def SMA(values, timeperiod):
            if len(values) < timeperiod:
                return [None] * len(values)
            result = []
            for i in range(len(values)):
                if i < timeperiod - 1:
                    result.append(None)
                else:
                    sma = sum(values[i-timeperiod+1:i+1]) / timeperiod
                    result.append(sma)
            return result

        @staticmethod
        def RSI(values, timeperiod):
            if len(values) < timeperiod + 1:
                return [None] * len(values)
            result = []
            for i in range(len(values)):
                if i < timeperiod:
                    result.append(None)
                else:
                    gains = []
                    losses = []
                    for j in range(i-timeperiod+1, i+1):
                        change = values[j] - values[j-1]
                        if change > 0:
                            gains.append(change)
                        else:
                            losses.append(abs(change))
                    avg_gain = sum(gains) / timeperiod if gains else 0
                    avg_loss = sum(losses) / timeperiod if losses else 0
                    if avg_loss == 0:
                        rsi = 100
                    else:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    result.append(rsi)
            return result

        @staticmethod
        def BBANDS(values, timeperiod, nbdevup, nbdevdn):
            if len(values) < timeperiod:
                return [None] * len(values), [None] * len(values), [None] * len(values)
            upper = []
            middle = []
            lower = []
            for i in range(len(values)):
                if i < timeperiod - 1:
                    upper.append(None)
                    middle.append(None)
                    lower.append(None)
                else:
                    period_values = values[i-timeperiod+1:i+1]
                    sma = sum(period_values) / timeperiod
                    variance = sum((x - sma) ** 2 for x in period_values) / timeperiod
                    std = math.sqrt(variance)
                    upper.append(sma + nbdevup * std)
                    middle.append(sma)
                    lower.append(sma - nbdevdn * std)
            return upper, middle, lower

        @staticmethod
        def MACD(values, fastperiod, slowperiod, signalperiod):
            if len(values) < slowperiod:
                return [None] * len(values), [None] * len(values), [None] * len(values)

            # 计算快线和慢线EMA
            ema_fast = MockTALib._ema(values, fastperiod)
            ema_slow = MockTALib._ema(values, slowperiod)

            # 计算MACD线
            macd_line = []
            for i in range(len(values)):
                if ema_fast[i] is None or ema_slow[i] is None:
                    macd_line.append(None)
                else:
                    macd_line.append(ema_fast[i] - ema_slow[i])

            # 计算信号线
            signal_line = MockTALib._ema([x for x in macd_line if x is not None], signalperiod)

            # 计算柱状图
            histogram = []
            signal_idx = 0
            for i in range(len(values)):
                if macd_line[i] is None or signal_idx >= len(signal_line):
                    histogram.append(None)
                else:
                    if signal_line[signal_idx] is None:
                        histogram.append(None)
                    else:
                        histogram.append(macd_line[i] - signal_line[signal_idx])
                    signal_idx += 1

            return macd_line, signal_line, histogram

        @staticmethod
        def _ema(values, period):
            if len(values) < period:
                return [None] * len(values)
            result = [None] * (period - 1)
            multiplier = 2 / (period + 1)
            result.append(sum(values[:period]) / period)
            for i in range(period, len(values)):
                ema = (values[i] * multiplier) + (result[-1] * (1 - multiplier))
                result.append(ema)
            return result

    # 用模拟版本替换talib
    talib = MockTALib()

from ..models.market_data import MarketData, OHLCV, Ticker
from ..models.short_signal import ShortSignalType, ShortSignalStrength
from ..config.config_manager import ConfigManager
from ..core.architecture import ShortAnalystArchitecture

logger = logging.getLogger(__name__)

class IndicatorCategory(Enum):
    """指标分类"""
    TREND_REVERSAL = "trend_reversal"      # 趋势反转指标
    OVERBOUGHT = "overbought"              # 超买指标
    RESISTANCE = "resistance"              # 压力位指标
    VOLUME = "volume"                      # 成交量指标
    SENTIMENT = "sentiment"                # 市场情绪指标
    MOMENTUM = "momentum"                  # 动量指标
    VOLATILITY = "volatility"              # 波动率指标

@dataclass
class IndicatorResult:
    """指标计算结果"""
    name: str
    category: IndicatorCategory
    value: float
    timestamp: datetime
    signal_type: Optional[ShortSignalType] = None
    signal_strength: Optional[ShortSignalStrength] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class IndicatorCache:
    """指标缓存"""
    symbol: str
    indicator_name: str
    timeframe: str
    values: List[float]
    timestamps: List[datetime]
    last_update: datetime
    ttl: timedelta

class BaseIndicator(ABC):
    """指标基类"""

    def __init__(self, name: str, category: IndicatorCategory, config: Dict[str, Any]):
        self.name = name
        self.category = category
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def calculate(self, data: MarketData) -> IndicatorResult:
        """计算指标"""
        pass

    def validate_data(self, data: MarketData) -> bool:
        """验证数据有效性"""
        if not data.ohlcv or len(data.ohlcv.close_prices) < self.get_min_data_length():
            return False
        return True

    @abstractmethod
    def get_min_data_length(self) -> int:
        """获取最小数据长度要求"""
        pass

class MovingAverageCrossover(BaseIndicator):
    """移动平均线交叉指标（死亡交叉）"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("MA_CROSSOVER", IndicatorCategory.TREND_REVERSAL, config)
        self.fast_period = config.get('fast_period', 5)
        self.slow_period = config.get('slow_period', 20)
        self.signal_threshold = config.get('signal_threshold', 0.02)

    def get_min_data_length(self) -> int:
        return self.slow_period

    async def calculate(self, data: MarketData) -> IndicatorResult:
        if not self.validate_data(data):
            return IndicatorResult(
                name=self.name,
                category=self.category,
                value=0.0,
                timestamp=data.timestamp,
                confidence=0.0
            )

        closes = data.ohlcv.close_prices

        # 计算移动平均线
        fast_ma = talib.SMA(closes, timeperiod=self.fast_period)
        slow_ma = talib.SMA(closes, timeperiod=self.slow_period)

        # 计算交叉信号
        current_fast = fast_ma[-1]
        current_slow = slow_ma[-1]
        previous_fast = fast_ma[-2] if len(fast_ma) > 1 else current_fast
        previous_slow = slow_ma[-2] if len(slow_ma) > 1 else current_slow

        # 检测死亡交叉（快线下穿慢线）
        death_cross = (previous_fast > previous_slow) and (current_fast < current_slow)

        # 计算信号强度
        signal_strength = self._calculate_signal_strength(current_fast, current_slow, data)

        return IndicatorResult(
            name=self.name,
            category=self.category,
            value=current_fast - current_slow,
            timestamp=data.timestamp,
            signal_type=ShortSignalType.TREND_REVERSAL if death_cross else None,
            signal_strength=signal_strength if death_cross else None,
            confidence=0.8 if death_cross else 0.1,
            metadata={
                'fast_ma': current_fast,
                'slow_ma': current_slow,
                'crossover_type': 'death_cross' if death_cross else 'no_cross'
            }
        )

    def _calculate_signal_strength(self, fast_ma: float, slow_ma: float, data: MarketData) -> ShortSignalStrength:
        """计算信号强度"""
        spread = abs(fast_ma - slow_ma) / slow_ma

        if spread > 0.05:
            return SignalStrength.STRONG
        elif spread > 0.03:
            return SignalStrength.MODERATE
        elif spread > 0.02:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

class RSIOverbought(BaseIndicator):
    """RSI超买指标"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("RSI_OVERBOUGHT", IndicatorCategory.OVERBOUGHT, config)
        self.period = config.get('period', 14)
        self.overbought_threshold = config.get('overbought_threshold', 70)
        self.oversold_threshold = config.get('oversold_threshold', 30)

    def get_min_data_length(self) -> int:
        return self.period + 1

    async def calculate(self, data: MarketData) -> IndicatorResult:
        if not self.validate_data(data):
            return IndicatorResult(
                name=self.name,
                category=self.category,
                value=50.0,
                timestamp=data.timestamp,
                confidence=0.0
            )

        closes = data.ohlcv.close_prices
        rsi = talib.RSI(closes, timeperiod=self.period)
        current_rsi = rsi[-1]

        # 检测超买信号
        overbought_signal = current_rsi > self.overbought_threshold

        # 计算信号强度
        signal_strength = self._calculate_signal_strength(current_rsi)

        return IndicatorResult(
            name=self.name,
            category=self.category,
            value=current_rsi,
            timestamp=data.timestamp,
            signal_type=ShortSignalType.OVERBOUGHT if overbought_signal else None,
            signal_strength=signal_strength if overbought_signal else None,
            confidence=min(1.0, (current_rsi - self.overbought_threshold) / 10) if overbought_signal else 0.1,
            metadata={
                'rsi_value': current_rsi,
                'overbought_threshold': self.overbought_threshold,
                'overbought_signal': overbought_signal
            }
        )

    def _calculate_signal_strength(self, rsi_value: float) -> ShortSignalStrength:
        """计算信号强度"""
        if rsi_value > 85:
            return SignalStrength.STRONG
        elif rsi_value > 78:
            return SignalStrength.MODERATE
        elif rsi_value > 72:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

class BollingerBandsUpper(BaseIndicator):
    """布林带上轨突破指标"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("BB_UPPER", IndicatorCategory.RESISTANCE, config)
        self.period = config.get('period', 20)
        self.std_dev = config.get('std_dev', 2)

    def get_min_data_length(self) -> int:
        return self.period

    async def calculate(self, data: MarketData) -> IndicatorResult:
        if not self.validate_data(data):
            return IndicatorResult(
                name=self.name,
                category=self.category,
                value=0.0,
                timestamp=data.timestamp,
                confidence=0.0
            )

        closes = data.ohlcv.close_prices
        upper_band, middle_band, lower_band = talib.BBANDS(
            closes, timeperiod=self.period, nbdevup=self.std_dev, nbdevdn=self.std_dev
        )

        current_price = closes[-1]
        current_upper = upper_band[-1]

        # 检测上轨突破
        upper_breakthrough = current_price > current_upper

        # 计算突破强度
        breakthrough_strength = (current_price - current_upper) / current_upper

        return IndicatorResult(
            name=self.name,
            category=self.category,
            value=breakthrough_strength,
            timestamp=data.timestamp,
            signal_type=ShortSignalType.RESISTANCE_BREAK if upper_breakthrough else None,
            signal_strength=self._calculate_signal_strength(breakthrough_strength) if upper_breakthrough else None,
            confidence=min(1.0, breakthrough_strength * 10) if upper_breakthrough else 0.1,
            metadata={
                'current_price': current_price,
                'upper_band': current_upper,
                'breakthrough': upper_breakthrough,
                'breakthrough_strength': breakthrough_strength
            }
        )

    def _calculate_signal_strength(self, strength: float) -> ShortSignalStrength:
        """计算信号强度"""
        if strength > 0.05:
            return SignalStrength.STRONG
        elif strength > 0.03:
            return SignalStrength.MODERATE
        elif strength > 0.015:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

class VolumePriceDivergence(BaseIndicator):
    """量价背离指标"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("VOLUME_PRICE_DIVERGENCE", IndicatorCategory.VOLUME, config)
        self.lookback_period = config.get('lookback_period', 5)

    def get_min_data_length(self) -> int:
        return self.lookback_period + 1

    async def calculate(self, data: MarketData) -> IndicatorResult:
        if not self.validate_data(data):
            return IndicatorResult(
                name=self.name,
                category=self.category,
                value=0.0,
                timestamp=data.timestamp,
                confidence=0.0
            )

        closes = data.ohlcv.close_prices
        volumes = data.ohlcv.volumes

        # 计算价格和成交量的变化率
        price_slice = closes[-self.lookback_period-1:]
        volume_slice = volumes[-self.lookback_period-1:]

        price_changes = []
        volume_changes = []

        for i in range(1, len(price_slice)):
            price_changes.append((price_slice[i] - price_slice[i-1]) / price_slice[i-1])
            volume_changes.append((volume_slice[i] - volume_slice[i-1]) / volume_slice[i-1])

        # 检测量价背离（价格上涨但成交量下降）
        divergence = sum(price_changes) / len(price_changes) > 0 and sum(volume_changes) / len(volume_changes) < 0

        # 计算背离强度
        divergence_strength = abs(sum(price_changes) / len(price_changes) - sum(volume_changes) / len(volume_changes))

        return IndicatorResult(
            name=self.name,
            category=self.category,
            value=divergence_strength,
            timestamp=data.timestamp,
            signal_type=ShortSignalType.VOLUME_DIVERGENCE if divergence else None,
            signal_strength=self._calculate_signal_strength(divergence_strength) if divergence else None,
            confidence=min(1.0, divergence_strength * 5) if divergence else 0.1,
            metadata={
                'price_change': np.mean(price_changes),
                'volume_change': np.mean(volume_changes),
                'divergence': divergence,
                'divergence_strength': divergence_strength
            }
        )

    def _calculate_signal_strength(self, strength: float) -> ShortSignalStrength:
        """计算信号强度"""
        if strength > 0.1:
            return SignalStrength.STRONG
        elif strength > 0.06:
            return SignalStrength.MODERATE
        elif strength > 0.03:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

class MACDDivergence(BaseIndicator):
    """MACD顶背离指标"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("MACD_DIVERGENCE", IndicatorCategory.TREND_REVERSAL, config)
        self.fast_period = config.get('fast_period', 12)
        self.slow_period = config.get('slow_period', 26)
        self.signal_period = config.get('signal_period', 9)
        self.lookback_period = config.get('lookback_period', 5)

    def get_min_data_length(self) -> int:
        return self.slow_period + self.signal_period + self.lookback_period

    async def calculate(self, data: MarketData) -> IndicatorResult:
        if not self.validate_data(data):
            return IndicatorResult(
                name=self.name,
                category=self.category,
                value=0.0,
                timestamp=data.timestamp,
                confidence=0.0
            )

        closes = data.ohlcv.close_prices

        # 计算MACD
        macd, signal, hist = talib.MACD(
            closes, fastperiod=self.fast_period, slowperiod=self.slow_period, signalperiod=self.signal_period
        )

        # 获取最近的数据
        recent_prices = closes[-self.lookback_period:]
        recent_hist = hist[-self.lookback_period:]

        # 检测顶背离（价格创新高但MACD柱状图没有）
        price_high = max(recent_prices)
        current_price = recent_prices[-1]
        hist_high = max(recent_hist)
        current_hist = recent_hist[-1]

        divergence = (current_price > price_high * 0.99) and (current_hist < hist_high * 0.9)

        # 计算背离强度
        divergence_strength = abs(hist_high - current_hist) / abs(hist_high) if hist_high != 0 else 0

        return IndicatorResult(
            name=self.name,
            category=self.category,
            value=divergence_strength,
            timestamp=data.timestamp,
            signal_type=ShortSignalType.MACD_DIVERGENCE if divergence else None,
            signal_strength=self._calculate_signal_strength(divergence_strength) if divergence else None,
            confidence=min(1.0, divergence_strength * 2) if divergence else 0.1,
            metadata={
                'current_price': current_price,
                'price_high': price_high,
                'current_hist': current_hist,
                'hist_high': hist_high,
                'divergence': divergence
            }
        )

    def _calculate_signal_strength(self, strength: float) -> ShortSignalStrength:
        """计算信号强度"""
        if strength > 0.3:
            return SignalStrength.STRONG
        elif strength > 0.2:
            return SignalStrength.MODERATE
        elif strength > 0.1:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

class ShortTechnicalIndicatorsEngine:
    """做空技术指标引擎"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.indicators: Dict[str, BaseIndicator] = {}
        self.cache: Dict[str, IndicatorCache] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger(__name__)

        # 初始化指标
        self._initialize_indicators()

    def _initialize_indicators(self):
        """初始化技术指标"""
        indicator_configs = self.config_manager.get_config().indicators

        # 趋势反转指标
        self.indicators['ma_crossover'] = MovingAverageCrossover(
            indicator_configs.get('ma_crossover', {})
        )
        self.indicators['macd_divergence'] = MACDDivergence(
            indicator_configs.get('macd_divergence', {})
        )

        # 超买指标
        self.indicators['rsi_overbought'] = RSIOverbought(
            indicator_configs.get('rsi_overbought', {})
        )

        # 压力位指标
        self.indicators['bb_upper'] = BollingerBandsUpper(
            indicator_configs.get('bb_upper', {})
        )

        # 成交量指标
        self.indicators['volume_divergence'] = VolumePriceDivergence(
            indicator_configs.get('volume_divergence', {})
        )

    async def calculate_all_indicators(self, data: MarketData) -> List[IndicatorResult]:
        """计算所有技术指标"""
        self.logger.info(f"开始计算所有技术指标 - {data.symbol}")

        tasks = []
        for name, indicator in self.indicators.items():
            task = asyncio.create_task(indicator.calculate(data))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"指标计算失败 {list(self.indicators.keys())[i]}: {result}")
            else:
                valid_results.append(result)

        # 更新缓存
        self._update_cache(data.symbol, valid_results)

        self.logger.info(f"技术指标计算完成 - {data.symbol}, 成功计算 {len(valid_results)} 个指标")
        return valid_results

    async def calculate_indicator(self, indicator_name: str, data: MarketData) -> Optional[IndicatorResult]:
        """计算单个指标"""
        if indicator_name not in self.indicators:
            self.logger.error(f"未找到指标: {indicator_name}")
            return None

        try:
            # 检查缓存
            cache_key = f"{data.symbol}_{indicator_name}_{data.timeframe}"
            if cache_key in self.cache:
                cached_result = self._get_from_cache(cache_key, data.timestamp)
                if cached_result:
                    return cached_result

            # 计算指标
            result = await self.indicators[indicator_name].calculate(data)

            # 更新缓存
            self._update_cache(data.symbol, [result])

            return result

        except Exception as e:
            self.logger.error(f"计算指标 {indicator_name} 失败: {e}")
            return None

    def _update_cache(self, symbol: str, results: List[IndicatorResult]):
        """更新指标缓存"""
        for result in results:
            cache_key = f"{symbol}_{result.name}"

            if cache_key in self.cache:
                # 更新现有缓存
                cache = self.cache[cache_key]
                cache.values.append(result.value)
                cache.timestamps.append(result.timestamp)
                cache.last_update = result.timestamp

                # 保持缓存大小
                if len(cache.values) > 1000:
                    cache.values = cache.values[-500:]
                    cache.timestamps = cache.timestamps[-500:]
            else:
                # 创建新缓存
                self.cache[cache_key] = IndicatorCache(
                    symbol=symbol,
                    indicator_name=result.name,
                    timeframe="1h",  # 默认时间框架
                    values=[result.value],
                    timestamps=[result.timestamp],
                    last_update=result.timestamp,
                    ttl=timedelta(hours=1)
                )

    def _get_from_cache(self, cache_key: str, timestamp: datetime) -> Optional[IndicatorResult]:
        """从缓存获取指标结果"""
        if cache_key not in self.cache:
            return None

        cache = self.cache[cache_key]

        # 检查缓存是否过期
        if timestamp - cache.last_update > cache.ttl:
            del self.cache[cache_key]
            return None

        # 返回最新的值
        if cache.values:
            return IndicatorResult(
                name=cache.indicator_name,
                category=self.indicators[cache.indicator_name].category,
                value=cache.values[-1],
                timestamp=cache.timestamps[-1],
                confidence=0.8  # 缓存结果的置信度稍低
            )

        return None

    async def get_short_signals(self, data: MarketData) -> List[IndicatorResult]:
        """获取做空信号"""
        results = await self.calculate_all_indicators(data)

        # 筛选出有信号的指标
        signals = [result for result in results if result.signal_type is not None]

        self.logger.info(f"检测到 {len(signals)} 个做空信号 - {data.symbol}")
        return signals

    def get_indicator_summary(self, symbol: str) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {
            'symbol': symbol,
            'total_indicators': len(self.indicators),
            'cached_indicators': len([k for k in self.cache.keys() if k.startswith(symbol)]),
            'last_update': None,
            'signals': []
        }

        # 获取最新的信号
        symbol_results = []
        for cache_key, cache in self.cache.items():
            if cache_key.startswith(symbol) and cache.values:
                latest_value = cache.values[-1]
                latest_timestamp = cache.timestamps[-1]

                indicator_name = cache_key.replace(f"{symbol}_", "")
                if indicator_name in self.indicators:
                    indicator = self.indicators[indicator_name]

                    # 简单的信号判断逻辑
                    signal_type = self._determine_signal(indicator, latest_value)

                    symbol_results.append({
                        'indicator': indicator_name,
                        'category': indicator.category.value,
                        'value': latest_value,
                        'timestamp': latest_timestamp,
                        'signal_type': signal_type.value if signal_type else None
                    })

        if symbol_results:
            summary['last_update'] = max(r['timestamp'] for r in symbol_results)
            summary['signals'] = [r for r in symbol_results if r['signal_type'] is not None]

        return summary

    def _determine_signal(self, indicator: BaseIndicator, value: float) -> Optional[ShortSignalType]:
        """基于指标值确定信号类型"""
        # 这里可以实现更复杂的信号判断逻辑
        # 现在提供基本的判断逻辑

        if isinstance(indicator, MovingAverageCrossover):
            if value < -0.02:  # 快线明显低于慢线
                return ShortSignalType.TREND_REVERSAL
        elif isinstance(indicator, RSIOverbought):
            if value > 70:  # RSI超买
                return ShortSignalType.OVERBOUGHT
        elif isinstance(indicator, BollingerBandsUpper):
            if value > 0:  # 价格突破上轨
                return ShortSignalType.RESISTANCE_BREAK
        elif isinstance(indicator, VolumePriceDivergence):
            if value > 0.05:  # 明显的量价背离
                return ShortSignalType.VOLUME_DIVERGENCE
        elif isinstance(indicator, MACDDivergence):
            if value > 0.1:  # 明显的MACD背离
                return ShortSignalType.MACD_DIVERGENCE

        return None

    def clear_cache(self, symbol: Optional[str] = None):
        """清除缓存"""
        if symbol:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(symbol)]
            for key in keys_to_remove:
                del self.cache[key]
            self.logger.info(f"已清除 {symbol} 的指标缓存")
        else:
            self.cache.clear()
            self.logger.info("已清除所有指标缓存")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'total_cache_entries': len(self.cache),
            'cache_size_mb': sum(len(str(cache)) for cache in self.cache.values()) / 1024 / 1024,
            'oldest_cache': min(cache.last_update for cache in self.cache.values()) if self.cache else None,
            'newest_cache': max(cache.last_update for cache in self.cache.values()) if self.cache else None,
            'symbols_cached': len(set(cache.symbol for cache in self.cache.values()))
        }

    async def close(self):
        """关闭引擎"""
        self.executor.shutdown(wait=True)
        self.cache.clear()
        self.logger.info("做空技术指标引擎已关闭")

# 使用示例
async def example_usage():
    """使用示例"""
    config_manager = ConfigManager()
    engine = ShortTechnicalIndicatorsEngine(config_manager)

    # 创建示例市场数据
    market_data = MarketData(
        symbol="BTC/USDT",
        timestamp=datetime.now(),
        timeframe="1h",
        ohlcv=OHLCV(
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)],
            open_prices=[40000 + i * 100 for i in range(100)],
            high_prices=[40500 + i * 100 for i in range(100)],
            low_prices=[39500 + i * 100 for i in range(100)],
            close_prices=[40200 + i * 100 for i in range(100)],
            volumes=[1000000 + i * 10000 for i in range(100)]
        )
    )

    try:
        # 计算所有指标
        results = await engine.calculate_all_indicators(market_data)
        print(f"计算了 {len(results)} 个指标")

        # 获取做空信号
        signals = await engine.get_short_signals(market_data)
        print(f"发现 {len(signals)} 个做空信号")

        for signal in signals:
            print(f"信号: {signal.signal_type.value}, 强度: {signal.signal_strength.value if signal.signal_strength else 'N/A'}")

        # 获取指标摘要
        summary = engine.get_indicator_summary("BTC/USDT")
        print(f"指标摘要: {summary}")

        # 查看缓存统计
        cache_stats = engine.get_cache_stats()
        print(f"缓存统计: {cache_stats}")

    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(example_usage())
"""
智能做空信号识别系统
整合多个技术指标生成高质量做空信号

核心功能：
1. 多指标信号融合
2. 信号强度评估
3. 置信度计算
4. 信号过滤和优先级排序
5. 信号历史追踪
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque

from ..indicators.indicator_engine import (
    ShortTechnicalIndicatorsEngine,
    IndicatorResult,
    IndicatorCategory,
    ShortSignalType,
    ShortSignalStrength
)

class SignalFusionMethod(Enum):
    """信号融合方法"""
    WEIGHTED_SUM = "weighted_sum"      # 加权求和
    CONSENSUS = "consensus"            # 共识投票
    HIERARCHICAL = "hierarchical"      # 分层融合
    ML_BASED = "ml_based"              # 机器学习（预留）


# 临时MarketData类型别名
class MockMarketData:
    def __init__(self, symbol, timestamp, ohlcv, source="test"):
        self.symbol = symbol
        self.timestamp = timestamp
        self.ohlcv = ohlcv
        self.source = source

MarketData = MockMarketData


@dataclass
class SignalComponent:
    """信号组成部分"""
    indicator_name: str
    category: IndicatorCategory
    weight: float
    signal_type: Optional[ShortSignalType]
    signal_strength: Optional[ShortSignalStrength]
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusionSignal:
    """融合后的做空信号"""
    signal_id: str
    signal_type: ShortSignalType
    signal_strength: ShortSignalStrength
    overall_confidence: float
    fusion_method: SignalFusionMethod
    components: List[SignalComponent]
    market_data: MarketData
    timestamp: datetime
    risk_score: float
    expected_duration: str
    supporting_indicators: Set[str]
    conflicting_indicators: Set[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SignalFusionConfig:
    """信号融合配置"""

    def __init__(self, config: Dict[str, Any]):
        self.fusion_method = SignalFusionMethod(config.get('fusion_method', 'weighted_sum'))

        # 指标权重配置
        self.indicator_weights = config.get('indicator_weights', {
            'MA_CROSSOVER': 0.25,
            'RSI_OVERBOUGHT': 0.20,
            'BOLLINGER_UPPER': 0.20,
            'VOLUME_DIVERGENCE': 0.15,
            'MACD_DIVERGENCE': 0.20
        })

        # 信号过滤阈值
        self.min_confidence_threshold = config.get('min_confidence_threshold', 0.7)
        self.min_supporting_indicators = config.get('min_supporting_indicators', 2)
        self.max_conflicting_indicators = config.get('max_conflicting_indicators', 1)

        # 时间窗口配置
        self.signal_time_window = config.get('signal_time_window', 300)  # 5分钟
        self.historical_window = config.get('historical_window', 86400)  # 24小时

        # 风险评估权重
        self.risk_weights = config.get('risk_weights', {
            'market_volatility': 0.3,
            'signal_consistency': 0.4,
            'technical_confirmation': 0.3
        })

        # 分层融合配置
        self.hierarchy_levels = config.get('hierarchy_levels', {
            'primary': ['MA_CROSSOVER', 'RSI_OVERBOUGHT'],
            'secondary': ['BOLLINGER_UPPER', 'MACD_DIVERGENCE'],
            'confirmatory': ['VOLUME_DIVERGENCE']
        })


class IntelligentSignalRecognition:
    """智能做空信号识别系统"""

    def __init__(self, indicator_engine: ShortTechnicalIndicatorsEngine, config: Dict[str, Any]):
        self.indicator_engine = indicator_engine
        self.fusion_config = SignalFusionConfig(config)
        self.logger = logging.getLogger(__name__)

        # 信号历史追踪
        self.signal_history: deque = deque(maxlen=1000)
        self.recent_signals: Dict[str, FusionSignal] = {}

        # 统计信息
        self.signal_stats = defaultdict(int)
        self.performance_metrics = {
            'total_signals': 0,
            'successful_signals': 0,
            'failed_signals': 0,
            'avg_confidence': 0.0,
            'avg_duration': 0.0
        }

        # 缓存机制
        self._indicator_cache: Dict[str, Tuple[List[IndicatorResult], datetime]] = {}
        self._cache_ttl = 60  # 1分钟缓存

    async def recognize_signals(self, market_data: MarketData) -> List[FusionSignal]:
        """识别做空信号"""
        try:
            # 获取所有指标结果
            indicator_results = await self._get_indicator_results(market_data)

            if not indicator_results:
                self.logger.warning("未获得有效的指标结果")
                return []

            # 融合信号
            fusion_signals = await self._fuse_signals(indicator_results, market_data)

            # 过滤和排序信号
            filtered_signals = self._filter_and_rank_signals(fusion_signals)

            # 更新历史记录
            self._update_signal_history(filtered_signals)

            return filtered_signals

        except Exception as e:
            self.logger.error(f"信号识别失败: {e}")
            return []

    async def _get_indicator_results(self, market_data: MarketData) -> List[IndicatorResult]:
        """获取指标结果（带缓存）"""
        cache_key = f"{market_data.symbol}_{market_data.timestamp}"

        # 检查缓存
        if cache_key in self._indicator_cache:
            cached_results, cache_time = self._indicator_cache[cache_key]
            if (datetime.now() - cache_time).total_seconds() < self._cache_ttl:
                return cached_results

        # 计算指标
        indicator_results = await self.indicator_engine.calculate_all_indicators(market_data)

        # 更新缓存
        self._indicator_cache[cache_key] = (indicator_results, datetime.now())

        return indicator_results

    async def _fuse_signals(self, indicator_results: List[IndicatorResult],
                          market_data: MarketData) -> List[FusionSignal]:
        """融合信号"""
        fusion_signals = []

        if self.fusion_config.fusion_method == SignalFusionMethod.WEIGHTED_SUM:
            fusion_signals = await self._weighted_sum_fusion(indicator_results, market_data)
        elif self.fusion_config.fusion_method == SignalFusionMethod.CONSENSUS:
            fusion_signals = await self._consensus_fusion(indicator_results, market_data)
        elif self.fusion_config.fusion_method == SignalFusionMethod.HIERARCHICAL:
            fusion_signals = await self._hierarchical_fusion(indicator_results, market_data)

        return fusion_signals

    async def _weighted_sum_fusion(self, indicator_results: List[IndicatorResult],
                                 market_data: MarketData) -> List[FusionSignal]:
        """加权求和融合"""
        fusion_signals = []

        # 按信号类型分组
        signal_groups = defaultdict(list)
        for result in indicator_results:
            if result.signal_type is not None:
                signal_groups[result.signal_type].append(result)

        # 对每组信号进行融合
        for signal_type, signals in signal_groups.items():
            fusion_signal = self._create_weighted_fusion_signal(
                signal_type, signals, market_data
            )
            if fusion_signal:
                fusion_signals.append(fusion_signal)

        return fusion_signals

    def _create_weighted_fusion_signal(self, signal_type: ShortSignalType,
                                      signals: List[IndicatorResult],
                                      market_data: MarketData) -> Optional[FusionSignal]:
        """创建加权融合信号"""
        if not signals:
            return None

        # 计算加权置信度
        total_weight = 0.0
        weighted_confidence = 0.0
        components = []

        for signal in signals:
            weight = self.fusion_config.indicator_weights.get(signal.name, 0.1)
            total_weight += weight
            weighted_confidence += signal.confidence * weight

            component = SignalComponent(
                indicator_name=signal.name,
                category=signal.category,
                weight=weight,
                signal_type=signal.signal_type,
                signal_strength=signal.signal_strength,
                confidence=signal.confidence,
                timestamp=signal.timestamp,
                metadata=signal.metadata
            )
            components.append(component)

        if total_weight == 0:
            return None

        overall_confidence = weighted_confidence / total_weight

        # 计算信号强度
        signal_strength = self._calculate_overall_signal_strength(signals)

        # 计算风险分数
        risk_score = self._calculate_risk_score(components, market_data)

        # 识别支持和冲突指标
        supporting_indicators = {c.indicator_name for c in components}
        conflicting_indicators = self._identify_conflicting_indicators(components)

        return FusionSignal(
            signal_id=f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal_type.value}",
            signal_type=signal_type,
            signal_strength=signal_strength,
            overall_confidence=overall_confidence,
            fusion_method=SignalFusionMethod.WEIGHTED_SUM,
            components=components,
            market_data=market_data,
            timestamp=datetime.now(),
            risk_score=risk_score,
            expected_duration=self._estimate_duration(signal_type, components),
            supporting_indicators=supporting_indicators,
            conflicting_indicators=conflicting_indicators,
            metadata={
                'total_weight': total_weight,
                'signal_count': len(signals),
                'method_details': 'weighted_sum_fusion'
            }
        )

    async def _consensus_fusion(self, indicator_results: List[IndicatorResult],
                              market_data: MarketData) -> List[FusionSignal]:
        """共识投票融合"""
        fusion_signals = []

        # 统计信号投票
        signal_votes = defaultdict(list)
        for result in indicator_results:
            if result.signal_type is not None:
                signal_votes[result.signal_type].append(result)

        # 对每种信号类型计算共识
        for signal_type, votes in signal_votes.items():
            # 计算共识分数
            consensus_score = len(votes) / len(indicator_results)

            if consensus_score >= 0.4:  # 至少40%的指标同意
                fusion_signal = self._create_consensus_signal(
                    signal_type, votes, consensus_score, market_data
                )
                if fusion_signal:
                    fusion_signals.append(fusion_signal)

        return fusion_signals

    def _create_consensus_signal(self, signal_type: ShortSignalType,
                              votes: List[IndicatorResult],
                              consensus_score: float,
                              market_data: MarketData) -> Optional[FusionSignal]:
        """创建共识信号"""
        avg_confidence = sum(v.confidence for v in votes) / len(votes)

        components = []
        for vote in votes:
            component = SignalComponent(
                indicator_name=vote.name,
                category=vote.category,
                weight=1.0 / len(votes),  # 均等权重
                signal_type=vote.signal_type,
                signal_strength=vote.signal_strength,
                confidence=vote.confidence,
                timestamp=vote.timestamp,
                metadata=vote.metadata
            )
            components.append(component)

        signal_strength = self._calculate_overall_signal_strength(votes)
        risk_score = self._calculate_risk_score(components, market_data)

        return FusionSignal(
            signal_id=f"consensus_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal_type.value}",
            signal_type=signal_type,
            signal_strength=signal_strength,
            overall_confidence=avg_confidence * consensus_score,
            fusion_method=SignalFusionMethod.CONSENSUS,
            components=components,
            market_data=market_data,
            timestamp=datetime.now(),
            risk_score=risk_score,
            expected_duration=self._estimate_duration(signal_type, components),
            supporting_indicators={c.indicator_name for c in components},
            conflicting_indicators=self._identify_conflicting_indicators(components),
            metadata={
                'consensus_score': consensus_score,
                'vote_count': len(votes),
                'method_details': 'consensus_fusion'
            }
        )

    async def _hierarchical_fusion(self, indicator_results: List[IndicatorResult],
                                 market_data: MarketData) -> List[FusionSignal]:
        """分层融合"""
        fusion_signals = []

        # 按层级分组
        hierarchy_groups = defaultdict(list)
        for result in indicator_results:
            for level, indicators in self.fusion_config.hierarchy_levels.items():
                if result.name in indicators:
                    hierarchy_groups[level].append(result)

        # 主层级信号优先
        primary_signals = hierarchy_groups.get('primary', [])
        if not primary_signals:
            return fusion_signals

        # 对每个主信号进行验证
        for primary_signal in primary_signals:
            if primary_signal.signal_type is None:
                continue

            # 获取次级和确认层级的支持
            secondary_signals = hierarchy_groups.get('secondary', [])
            confirmatory_signals = hierarchy_groups.get('confirmatory', [])

            fusion_signal = self._create_hierarchical_signal(
                primary_signal, secondary_signals, confirmatory_signals, market_data
            )
            if fusion_signal:
                fusion_signals.append(fusion_signal)

        return fusion_signals

    def _create_hierarchical_signal(self, primary_signal: IndicatorResult,
                                   secondary_signals: List[IndicatorResult],
                                   confirmatory_signals: List[IndicatorResult],
                                   market_data: MarketData) -> Optional[FusionSignal]:
        """创建分层融合信号"""
        components = []

        # 添加主信号
        primary_component = SignalComponent(
            indicator_name=primary_signal.name,
            category=primary_signal.category,
            weight=0.5,  # 主信号权重50%
            signal_type=primary_signal.signal_type,
            signal_strength=primary_signal.signal_strength,
            confidence=primary_signal.confidence,
            timestamp=primary_signal.timestamp,
            metadata=primary_signal.metadata
        )
        components.append(primary_component)

        # 添加次级信号
        secondary_weight = 0.3 / len(secondary_signals) if secondary_signals else 0
        for signal in secondary_signals:
            if signal.signal_type == primary_signal.signal_type:
                component = SignalComponent(
                    indicator_name=signal.name,
                    category=signal.category,
                    weight=secondary_weight,
                    signal_type=signal.signal_type,
                    signal_strength=signal.signal_strength,
                    confidence=signal.confidence,
                    timestamp=signal.timestamp,
                    metadata=signal.metadata
                )
                components.append(component)

        # 添加确认信号
        confirmatory_weight = 0.2 / len(confirmatory_signals) if confirmatory_signals else 0
        for signal in confirmatory_signals:
            if signal.signal_type == primary_signal.signal_type:
                component = SignalComponent(
                    indicator_name=signal.name,
                    category=signal.category,
                    weight=confirmatory_weight,
                    signal_type=signal.signal_type,
                    signal_strength=signal.signal_strength,
                    confidence=signal.confidence,
                    timestamp=signal.timestamp,
                    metadata=signal.metadata
                )
                components.append(component)

        # 计算总体置信度
        overall_confidence = sum(c.weight * c.confidence for c in components)

        # 计算信号强度
        all_signals = [primary_signal] + secondary_signals + confirmatory_signals
        signal_strength = self._calculate_overall_signal_strength(all_signals)

        # 计算风险分数
        risk_score = self._calculate_risk_score(components, market_data)

        return FusionSignal(
            signal_id=f"hierarchical_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{primary_signal.signal_type.value}",
            signal_type=primary_signal.signal_type,
            signal_strength=signal_strength,
            overall_confidence=overall_confidence,
            fusion_method=SignalFusionMethod.HIERARCHICAL,
            components=components,
            market_data=market_data,
            timestamp=datetime.now(),
            risk_score=risk_score,
            expected_duration=self._estimate_duration(primary_signal.signal_type, components),
            supporting_indicators={c.indicator_name for c in components},
            conflicting_indicators=self._identify_conflicting_indicators(components),
            metadata={
                'hierarchy_level': 'validated',
                'primary_signal': primary_signal.name,
                'secondary_count': len(secondary_signals),
                'confirmatory_count': len(confirmatory_signals),
                'method_details': 'hierarchical_fusion'
            }
        )

    def _calculate_overall_signal_strength(self, signals: List[IndicatorResult]) -> ShortSignalStrength:
        """计算整体信号强度"""
        if not signals:
            return ShortSignalStrength.VERY_WEAK

        # 统计各强度等级的数量
        strength_counts = defaultdict(int)
        for signal in signals:
            if signal.signal_strength:
                strength_counts[signal.signal_strength] += 1

        if not strength_counts:
            return ShortSignalStrength.VERY_WEAK

        # 计算加权分数
        strength_scores = {
            ShortSignalStrength.STRONG: 4,
            ShortSignalStrength.MODERATE: 3,
            ShortSignalStrength.WEAK: 2,
            ShortSignalStrength.VERY_WEAK: 1
        }

        total_score = sum(strength_counts[strength] * strength_scores[strength]
                         for strength in strength_counts)
        avg_score = total_score / len(signals)

        # 转换为强度等级
        if avg_score >= 3.5:
            return ShortSignalStrength.STRONG
        elif avg_score >= 2.5:
            return ShortSignalStrength.MODERATE
        elif avg_score >= 1.5:
            return ShortSignalStrength.WEAK
        else:
            return ShortSignalStrength.VERY_WEAK

    def _calculate_risk_score(self, components: List[SignalComponent],
                             market_data: MarketData) -> float:
        """计算风险分数 (0-1, 1为最高风险)"""
        risk_factors = []

        # 1. 市场波动率风险
        volatility_risk = self._calculate_volatility_risk(market_data)
        risk_factors.append(volatility_risk * self.fusion_config.risk_weights['market_volatility'])

        # 2. 信号一致性风险
        consistency_risk = self._calculate_consistency_risk(components)
        risk_factors.append(consistency_risk * self.fusion_config.risk_weights['signal_consistency'])

        # 3. 技术确认风险
        confirmation_risk = self._calculate_confirmation_risk(components)
        risk_factors.append(confirmation_risk * self.fusion_config.risk_weights['technical_confirmation'])

        return sum(risk_factors)

    def _calculate_volatility_risk(self, market_data: MarketData) -> float:
        """计算市场波动率风险"""
        if not market_data.ohlcv or len(market_data.ohlcv.close_prices) < 20:
            return 0.5  # 默认中等风险

        closes = market_data.ohlcv.close_prices[-20:]  # 最近20个价格

        # 计算价格标准差
        mean_price = sum(closes) / len(closes)
        variance = sum((price - mean_price) ** 2 for price in closes) / len(closes)
        std_dev = variance ** 0.5

        # 计算变异系数
        cv = std_dev / mean_price if mean_price > 0 else 0

        # 归一化到0-1
        return min(cv * 10, 1.0)  # 放大系数10

    def _calculate_consistency_risk(self, components: List[SignalComponent]) -> float:
        """计算信号一致性风险"""
        if len(components) <= 1:
            return 0.0

        # 计算置信度的标准差
        confidences = [c.confidence for c in components]
        mean_conf = sum(confidences) / len(confidences)
        variance = sum((conf - mean_conf) ** 2 for conf in confidences) / len(confidences)
        std_dev = variance ** 0.5

        # 标准差越大，一致性越差，风险越高
        return min(std_dev * 2, 1.0)  # 放大系数2

    def _calculate_confirmation_risk(self, components: List[SignalComponent]) -> float:
        """计算技术确认风险"""
        if not components:
            return 1.0

        # 检查信号类型的多样性
        signal_types = {c.signal_type for c in components if c.signal_type is not None}

        # 信号类型越少，确认度越低，风险越高
        if len(signal_types) == 0:
            return 1.0
        elif len(signal_types) == 1:
            return 0.3  # 单一信号类型，风险较高
        else:
            return 0.1  # 多种信号类型确认，风险较低

    def _identify_conflicting_indicators(self, components: List[SignalComponent]) -> Set[str]:
        """识别冲突指标"""
        conflicting = set()

        # 找出信号类型不同的指标
        signal_types = {}
        for component in components:
            if component.signal_type:
                if component.signal_type not in signal_types:
                    signal_types[component.signal_type] = []
                signal_types[component.signal_type].append(component.indicator_name)

        # 如果有多种信号类型，则它们互为冲突
        if len(signal_types) > 1:
            all_indicators = {c.indicator_name for c in components}
            conflicting = all_indicators  # 在这种情况下，所有指标都算作冲突

        return conflicting

    def _estimate_duration(self, signal_type: ShortSignalType,
                           components: List[SignalComponent]) -> str:
        """估计信号持续时间"""
        # 基于信号类型和指标数量估计持续时间
        base_durations = {
            ShortSignalType.TREND_REVERSAL: "4-8h",
            ShortSignalType.OVERBOUGHT_REVERSAL: "1-3h",
            ShortSignalType.BREAKOUT_FAILURE: "2-4h",
            ShortSignalType.DIVERGENCE: "3-6h"
        }

        base_duration = base_durations.get(signal_type, "2-4h")

        # 指标越多，持续时间越长
        indicator_count = len(components)
        if indicator_count >= 4:
            return f"Long ({base_duration})"
        elif indicator_count >= 2:
            return base_duration
        else:
            return f"Short ({base_duration})"

    def _filter_and_rank_signals(self, signals: List[FusionSignal]) -> List[FusionSignal]:
        """过滤和排序信号"""
        filtered = []

        for signal in signals:
            # 1. 置信度过滤
            if signal.overall_confidence < self.fusion_config.min_confidence_threshold:
                continue

            # 2. 支持指标数量过滤
            if len(signal.supporting_indicators) < self.fusion_config.min_supporting_indicators:
                continue

            # 3. 冲突指标数量过滤
            if len(signal.conflicting_indicators) > self.fusion_config.max_conflicting_indicators:
                continue

            # 4. 风险分数过滤
            if signal.risk_score > 0.8:  # 风险过高
                continue

            filtered.append(signal)

        # 按置信度和信号强度排序
        filtered.sort(key=lambda s: (s.overall_confidence, s.signal_strength.value), reverse=True)

        return filtered

    def _update_signal_history(self, signals: List[FusionSignal]):
        """更新信号历史"""
        for signal in signals:
            self.signal_history.append(signal)
            self.recent_signals[signal.signal_id] = signal

            # 更新统计信息
            self.signal_stats[signal.signal_type.value] += 1
            self.performance_metrics['total_signals'] += 1
            self.performance_metrics['avg_confidence'] = (
                (self.performance_metrics['avg_confidence'] * (self.performance_metrics['total_signals'] - 1) +
                 signal.overall_confidence) / self.performance_metrics['total_signals']
            )

    def get_signal_statistics(self) -> Dict[str, Any]:
        """获取信号统计信息"""
        return {
            'signal_stats': dict(self.signal_stats),
            'performance_metrics': self.performance_metrics,
            'recent_signal_count': len(self.recent_signals),
            'cache_size': len(self._indicator_cache)
        }

    def get_signal_by_id(self, signal_id: str) -> Optional[FusionSignal]:
        """根据ID获取信号"""
        return self.recent_signals.get(signal_id)

    def get_recent_signals(self, limit: int = 10) -> List[FusionSignal]:
        """获取最近的信号"""
        return list(self.signal_history)[-limit:]

    def clear_cache(self):
        """清除缓存"""
        self._indicator_cache.clear()
        self.logger.info("信号缓存已清除")
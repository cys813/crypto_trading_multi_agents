"""
做空信号模型定义

该模块定义了做空分析师代理中使用的各种信号类型和数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class ShortSignalType(Enum):
    """做空信号类型"""
    # 趋势反转信号
    TREND_REVERSAL = "trend_reversal"          # 趋势反转
    SUPPORT_BREAK = "support_break"              # 支撑位跌破
    DOUBLE_TOP = "double_top"                    # 双顶形态
    HEAD_SHOULDERS_TOP = "head_shoulders_top"    # 头肩顶

    # 超买信号
    RSI_OVERBOUGHT = "rsi_overbought"           # RSI超买
    KDJ_OVERBOUGHT = "kdj_overbought"           # KDJ超买
    BOLLINGER_UPPER = "bollinger_upper"         # 布林带上轨突破

    # 压力位信号
    RESISTANCE_TEST = "resistance_test"         # 压力位测试
    FIBONACCI_RESISTANCE = "fibonacci_resistance" # 斐波那契阻力位

    # 成交量信号
    VOLUME_DIVERGENCE = "volume_divergence"     # 成交量背离
    DISTRIBUTION_PATTERN = "distribution_pattern" # 派发形态

    # 情绪信号
    FEAR_GREED_EXTREME = "fear_greed_extreme"   # 恐惧贪婪指数极端
    SOCIAL_SENTIMENT_BEARISH = "social_sentiment_bearish"  # 社交媒体情绪看跌
    NEWS_SENTIMENT_NEGATIVE = "news_sentiment_negative"     # 新闻情绪负面

    # 市场结构信号
    MARKET_OVERHEATED = "market_overheated"     # 市场过热
    LEVERAGE_HIGH = "leverage_high"              # 杠杆率过高
    LIQUIDITY_DRYING = "liquidity_drying"       # 流动性枯竭


class ShortSignalStrength(Enum):
    """做空信号强度"""
    WEAK = 1      # 弱信号 (1-3分)
    MODERATE = 2  # 中等信号 (4-6分)
    STRONG = 3    # 强信号 (7-10分)

    @property
    def score_range(self) -> tuple:
        """返回对应的分数范围"""
        ranges = {
            ShortSignalStrength.WEAK: (1, 3),
            ShortSignalStrength.MODERATE: (4, 6),
            ShortSignalStrength.STRONG: (7, 10)
        }
        return ranges[self]

    @property
    def value(self) -> float:
        """返回中间值"""
        min_score, max_score = self.score_range
        return (min_score + max_score) / 2


class SignalReliability(Enum):
    """信号可靠性等级"""
    LOW = 1       # 低可靠性 (历史成功率 < 50%)
    MEDIUM = 2    # 中等可靠性 (历史成功率 50-70%)
    HIGH = 3      # 高可靠性 (历史成功率 > 70%)


@dataclass
class ShortSignal:
    """做空信号数据类"""
    # 必填字段（无默认值）
    signal_type: ShortSignalType
    symbol: str
    strength: ShortSignalStrength
    reliability: SignalReliability

    # 可选字段（有默认值）
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = field(default=None)

    # 信号详情
    confidence_score: float = field(default=0.0)  # 置信度分数 (0-1)
    price_level: Optional[float] = field(default=None)  # 建议做空价格
    stop_loss: Optional[float] = field(default=None)    # 止损价格
    take_profit: Optional[float] = field(default=None)  # 止盈价格

    # 技术指标值
    indicator_values: Dict[str, float] = field(default_factory=dict)
    market_conditions: Dict[str, Any] = field(default_factory=dict)

    # 风险评估
    risk_level: int = field(default=1)  # 风险等级 1-5
    liquidity_risk: float = field(default=0.0)  # 流动性风险 (0-1)
    short_squeeze_risk: float = field(default=0.0)  # 轧空风险 (0-1)

    # 历史表现
    historical_success_rate: float = field(default=0.0)  # 历史成功率
    sample_size: int = field(default=0)  # 样本数量

    # 附加信息
    description: str = field(default="")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if self.confidence_score < 0 or self.confidence_score > 1:
            raise ValueError("置信度分数必须在0-1之间")

        if self.risk_level < 1 or self.risk_level > 5:
            raise ValueError("风险等级必须在1-5之间")

        # 设置默认过期时间 (24小时)
        if self.expires_at is None:
            self.expires_at = self.detected_at.replace(hour=self.detected_at.hour + 24)

    @property
    def is_expired(self) -> bool:
        """检查信号是否已过期"""
        return datetime.now() > self.expires_at

    @property
    def time_to_expiry_hours(self) -> float:
        """距离过期的小时数"""
        return (self.expires_at - datetime.now()).total_seconds() / 3600

    @property
    def overall_score(self) -> float:
        """计算信号总体评分"""
        # 基于强度、可靠性、置信度的加权评分
        strength_weight = 0.4
        reliability_weight = 0.3
        confidence_weight = 0.3

        strength_score = self.strength.value / 10.0  # 归一化到0-1
        reliability_score = self.reliability.value / 3.0  # 归一化到0-1

        overall = (
            strength_score * strength_weight +
            reliability_score * reliability_weight +
            self.confidence_score * confidence_weight
        )

        return overall

    def validate(self) -> List[str]:
        """验证信号的有效性"""
        errors = []

        if not self.symbol:
            errors.append("交易对符号不能为空")

        if self.confidence_score < 0.5:  # 置信度过低
            errors.append("置信度过低")

        if self.historical_success_rate < 0.3:  # 历史成功率过低
            errors.append("历史成功率过低")

        if self.sample_size < 10:  # 样本数量过少
            errors.append("样本数量不足")

        if self.liquidity_risk > 0.8:  # 流动性风险过高
            errors.append("流动性风险过高")

        if self.short_squeeze_risk > 0.7:  # 轧空风险过高
            errors.append("轧空风险过高")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "symbol": self.symbol,
            "strength": self.strength.value,
            "reliability": self.reliability.value,
            "detected_at": self.detected_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "confidence_score": self.confidence_score,
            "price_level": self.price_level,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "indicator_values": self.indicator_values,
            "market_conditions": self.market_conditions,
            "risk_level": self.risk_level,
            "liquidity_risk": self.liquidity_risk,
            "short_squeeze_risk": self.short_squeeze_risk,
            "historical_success_rate": self.historical_success_rate,
            "sample_size": self.sample_size,
            "description": self.description,
            "overall_score": self.overall_score,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShortSignal':
        """从字典创建信号对象"""
        # 转换枚举值
        signal_type = ShortSignalType(data["signal_type"])
        strength = ShortSignalStrength(data["strength"])
        reliability = SignalReliability(data["reliability"])

        # 转换时间
        detected_at = datetime.fromisoformat(data["detected_at"])
        expires_at = datetime.fromisoformat(data["expires_at"])

        return cls(
            signal_id=data["signal_id"],
            signal_type=signal_type,
            symbol=data["symbol"],
            strength=strength,
            reliability=reliability,
            detected_at=detected_at,
            expires_at=expires_at,
            confidence_score=data["confidence_score"],
            price_level=data.get("price_level"),
            stop_loss=data.get("stop_loss"),
            take_profit=data.get("take_profit"),
            indicator_values=data.get("indicator_values", {}),
            market_conditions=data.get("market_conditions", {}),
            risk_level=data.get("risk_level", 1),
            liquidity_risk=data.get("liquidity_risk", 0.0),
            short_squeeze_risk=data.get("short_squeeze_risk", 0.0),
            historical_success_rate=data.get("historical_success_rate", 0.0),
            sample_size=data.get("sample_size", 0),
            description=data.get("description", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class ShortSignalPortfolio:
    """做空信号组合"""
    portfolio_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    signals: List[ShortSignal] = field(default_factory=list)

    # 组合统计
    total_signals: int = field(default=0)
    strong_signals: int = field(default=0)
    moderate_signals: int = field(default=0)
    weak_signals: int = field(default=0)

    # 风险指标
    average_risk_level: float = field(default=0.0)
    max_risk_level: int = field(default=1)
    liquidity_risk_score: float = field(default=0.0)

    # 预期表现
    expected_success_rate: float = field(default=0.0)
    confidence_score: float = field(default=0.0)

    def add_signal(self, signal: ShortSignal):
        """添加做空信号"""
        self.signals.append(signal)
        self._update_statistics()

    def remove_signal(self, signal_id: str):
        """移除做空信号"""
        self.signals = [s for s in self.signals if s.signal_id != signal_id]
        self._update_statistics()

    def _update_statistics(self):
        """更新组合统计信息"""
        if not self.signals:
            return

        self.total_signals = len(self.signals)

        # 统计信号强度分布
        self.strong_signals = len([s for s in self.signals if s.strength == ShortSignalStrength.STRONG])
        self.moderate_signals = len([s for s in self.signals if s.strength == ShortSignalStrength.MODERATE])
        self.weak_signals = len([s for s in self.signals if s.strength == ShortSignalStrength.WEAK])

        # 计算风险指标
        risk_levels = [s.risk_level for s in self.signals]
        self.average_risk_level = sum(risk_levels) / len(risk_levels)
        self.max_risk_level = max(risk_levels)

        liquidity_risks = [s.liquidity_risk for s in self.signals]
        self.liquidity_risk_score = sum(liquidity_risks) / len(liquidity_risks)

        # 计算预期表现
        success_rates = [s.historical_success_rate for s in self.signals if s.historical_success_rate > 0]
        if success_rates:
            self.expected_success_rate = sum(success_rates) / len(success_rates)

        confidence_scores = [s.confidence_score for s in self.signals]
        self.confidence_score = sum(confidence_scores) / len(confidence_scores)

    def get_signals_by_type(self, signal_type: ShortSignalType) -> List[ShortSignal]:
        """按类型获取信号"""
        return [s for s in self.signals if s.signal_type == signal_type]

    def get_high_confidence_signals(self, min_confidence: float = 0.7) -> List[ShortSignal]:
        """获取高置信度信号"""
        return [s for s in self.signals if s.confidence_score >= min_confidence]

    def get_low_risk_signals(self, max_risk_level: int = 2) -> List[ShortSignal]:
        """获取低风险信号"""
        return [s for s in self.signals if s.risk_level <= max_risk_level]

    def validate_portfolio(self) -> List[str]:
        """验证信号组合的有效性"""
        errors = []

        if not self.signals:
            errors.append("信号组合为空")

        if self.total_signals > 20:  # 信号过多
            errors.append("信号数量过多，建议精简")

        if self.max_risk_level > 4:  # 风险过高
            errors.append("存在高风险信号")

        if self.liquidity_risk_score > 0.7:  # 流动性风险过高
            errors.append("整体流动性风险过高")

        if self.expected_success_rate < 0.4:  # 预期成功率过低
            errors.append("预期成功率过低")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "portfolio_id": self.portfolio_id,
            "created_at": self.created_at.isoformat(),
            "signals": [signal.to_dict() for signal in self.signals],
            "total_signals": self.total_signals,
            "strong_signals": self.strong_signals,
            "moderate_signals": self.moderate_signals,
            "weak_signals": self.weak_signals,
            "average_risk_level": self.average_risk_level,
            "max_risk_level": self.max_risk_level,
            "liquidity_risk_score": self.liquidity_risk_score,
            "expected_success_rate": self.expected_success_rate,
            "confidence_score": self.confidence_score
        }
"""
市场数据模型定义

该模块定义了做空分析师代理中使用的市场数据结构。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
# 尝试导入pandas和numpy，如果不可用则使用模拟版本
try:
    import pandas as pd
except ImportError:
    # 创建模拟的pandas模块
    class MockPandas:
        @staticmethod
        def DataFrame(data=None):
            return data or []

    pd = MockPandas()

try:
    import numpy as np
except ImportError:
    # 创建模拟的numpy模块
    import math
    import random

    class MockNumpy:
        @staticmethod
        def array(data):
            return list(data)

        @staticmethod
        def mean(data):
            return sum(data) / len(data) if data else 0

        @staticmethod
        def std(data):
            if not data:
                return 0
            mean_val = sum(data) / len(data)
            variance = sum((x - mean_val) ** 2 for x in data) / len(data)
            return math.sqrt(variance)

    np = MockNumpy()


class MarketDataType(Enum):
    """市场数据类型"""
    OHLCV = "ohlcv"          # 开高低收成交量数据
    TICKER = "ticker"         # 行情数据
    ORDERBOOK = "orderbook"   # 订单簿数据
    TRADES = "trades"         # 交易数据
    LIQUIDITY = "liquidity"   # 流动性数据
    FUNDING_RATE = "funding_rate"  # 资金费率数据
    OPEN_INTEREST = "open_interest"  # 未平仓合约数据


class TimeFrame(Enum):
    """时间周期"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


@dataclass
class OHLCV:
    """开高低收成交量数据"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: TimeFrame

    # 可选字段
    quote_volume: Optional[float] = field(default=None)
    trade_count: Optional[int] = field(default=None)
    taker_buy_volume: Optional[float] = field(default=None)
    taker_buy_quote_volume: Optional[float] = field(default=None)

    @property
    def price_range(self) -> float:
        """价格区间"""
        return self.high - self.low

    @property
    def body_size(self) -> float:
        """实体大小"""
        return abs(self.close - self.open)

    @property
    def upper_shadow(self) -> float:
        """上影线长度"""
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self) -> float:
        """下影线长度"""
        return min(self.open, self.close) - self.low

    @property
    def is_green(self) -> bool:
        """是否为阳线"""
        return self.close > self.open

    @property
    def is_red(self) -> bool:
        """是否为阴线"""
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """是否为十字星"""
        return self.body_size / self.price_range < 0.1 if self.price_range > 0 else False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe.value,
            "quote_volume": self.quote_volume,
            "trade_count": self.trade_count,
            "taker_buy_volume": self.taker_buy_volume,
            "taker_buy_quote_volume": self.taker_buy_quote_volume
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OHLCV':
        """从字典创建对象"""
        return cls(
            symbol=data["symbol"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            timeframe=TimeFrame(data["timeframe"]),
            quote_volume=data.get("quote_volume"),
            trade_count=data.get("trade_count"),
            taker_buy_volume=data.get("taker_buy_volume"),
            taker_buy_quote_volume=data.get("taker_buy_quote_volume")
        )


@dataclass
class Ticker:
    """行情数据"""
    symbol: str
    timestamp: datetime
    last_price: float
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float

    # 计算
    spread: float = field(init=False)
    mid_price: float = field(init=False)
    volume_weighted_price: float = field(init=False)

    def __post_init__(self):
        """初始化后计算"""
        self.spread = self.ask_price - self.bid_price
        self.mid_price = (self.bid_price + self.ask_price) / 2
        self.volume_weighted_price = (
            (self.bid_price * self.bid_volume + self.ask_price * self.ask_volume) /
            (self.bid_volume + self.ask_volume)
        ) if (self.bid_volume + self.ask_volume) > 0 else self.mid_price

    @property
    def spread_percentage(self) -> float:
        """价差百分比"""
        return (self.spread / self.mid_price) * 100 if self.mid_price > 0 else 0

    @property
    def liquidity_score(self) -> float:
        """流动性评分 (0-1)"""
        # 基于买卖量和价差计算流动性
        total_volume = self.bid_volume + self.ask_volume
        spread_factor = max(0, 1 - self.spread_percentage / 1.0)  # 1%价差为基准
        volume_factor = min(1.0, total_volume / 1000000)  # 100万为基准

        return (spread_factor + volume_factor) / 2

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "last_price": self.last_price,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "bid_volume": self.bid_volume,
            "ask_volume": self.ask_volume,
            "spread": self.spread,
            "mid_price": self.mid_price,
            "spread_percentage": self.spread_percentage,
            "liquidity_score": self.liquidity_score
        }


@dataclass
class OrderBookLevel:
    """订单簿层级"""
    price: float
    volume: float
    count: Optional[int] = field(default=None)  # 订单数量


@dataclass
class OrderBook:
    """订单簿数据"""
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel]  # 买单
    asks: List[OrderBookLevel]  # 卖单

    @property
    def best_bid(self) -> Optional[OrderBookLevel]:
        """最佳买价"""
        return max(self.bids, key=lambda x: x.price) if self.bids else None

    @property
    def best_ask(self) -> Optional[OrderBookLevel]:
        """最佳卖价"""
        return min(self.asks, key=lambda x: x.price) if self.asks else None

    @property
    def mid_price(self) -> Optional[float]:
        """中间价格"""
        if self.best_bid and self.best_ask:
            return (self.best_bid.price + self.best_ask.price) / 2
        return None

    @property
    def spread(self) -> Optional[float]:
        """价差"""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None

    @property
    def total_bid_volume(self) -> float:
        """总买量"""
        return sum(level.volume for level in self.bids)

    @property
    def total_ask_volume(self) -> float:
        """总卖量"""
        return sum(level.volume for level in self.asks)

    @property
    def imbalance(self) -> float:
        """买卖不平衡 (-1到1)"""
        total_volume = self.total_bid_volume + self.total_ask_volume
        if total_volume == 0:
            return 0
        return (self.total_bid_volume - self.total_ask_volume) / total_volume

    def get_depth_data(self, depth: int = 10) -> Dict[str, List[Dict[str, float]]]:
        """获取深度数据"""
        return {
            "bids": [
                {"price": level.price, "volume": level.volume}
                for level in self.bids[:depth]
            ],
            "asks": [
                {"price": level.price, "volume": level.volume}
                for level in self.asks[:depth]
            ]
        }

    def calculate_liquidity_score(self) -> float:
        """计算流动性评分"""
        if not self.bids or not self.asks:
            return 0.0

        # 考虑价差、深度和订单数量
        spread_factor = max(0, 1 - (self.spread / self.mid_price) * 100) if self.mid_price else 0
        depth_factor = min(1.0, (self.total_bid_volume + self.total_ask_volume) / 1000000)
        count_factor = min(1.0, (len(self.bids) + len(self.asks)) / 100)

        return (spread_factor + depth_factor + count_factor) / 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bids": [{"price": level.price, "volume": level.volume, "count": level.count} for level in self.bids],
            "asks": [{"price": level.price, "volume": level.volume, "count": level.count} for level in self.asks],
            "best_bid": self.best_bid.price if self.best_bid else None,
            "best_ask": self.best_ask.price if self.best_ask else None,
            "mid_price": self.mid_price,
            "spread": self.spread,
            "total_bid_volume": self.total_bid_volume,
            "total_ask_volume": self.total_ask_volume,
            "imbalance": self.imbalance,
            "liquidity_score": self.calculate_liquidity_score()
        }


@dataclass
class Trade:
    """交易数据"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    side: str  # "buy" or "sell"

    # 可选字段
    trade_id: Optional[str] = field(default=None)
    order_id: Optional[str] = field(default=None)
    fee: Optional[float] = field(default=None)
    fee_currency: Optional[str] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "volume": self.volume,
            "side": self.side,
            "trade_id": self.trade_id,
            "order_id": self.order_id,
            "fee": self.fee,
            "fee_currency": self.fee_currency
        }


@dataclass
class LiquidityData:
    """流动性数据"""
    symbol: str
    timestamp: datetime
    liquidity_score: float  # 0-1
    volume_24h: float
    bid_ask_spread: float
    market_depth_usd: float
    volatility_24h: float

    # 流动性详情
    buy_pressure: float  # 买入压力 (0-1)
    sell_pressure: float  # 卖出压力 (0-1)
    large_orders_ratio: float  # 大单比例

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "liquidity_score": self.liquidity_score,
            "volume_24h": self.volume_24h,
            "bid_ask_spread": self.bid_ask_spread,
            "market_depth_usd": self.market_depth_usd,
            "volatility_24h": self.volatility_24h,
            "buy_pressure": self.buy_pressure,
            "sell_pressure": self.sell_pressure,
            "large_orders_ratio": self.large_orders_ratio
        }


@dataclass
class FundingRate:
    """资金费率数据"""
    symbol: str
    timestamp: datetime
    funding_rate: float
    mark_price: float
    index_price: float
    next_funding_time: datetime

    # 计算
    annualized_rate: float = field(init=False)

    def __post_init__(self):
        """初始化后计算"""
        # 年化费率 (假设8小时结算一次)
        self.annualized_rate = self.funding_rate * (365 * 3)

    @property
    def rate_percentage(self) -> float:
        """费率百分比"""
        return self.funding_rate * 100

    @property
    def annualized_percentage(self) -> float:
        """年化费率百分比"""
        return self.annualized_rate * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "funding_rate": self.funding_rate,
            "mark_price": self.mark_price,
            "index_price": self.index_price,
            "next_funding_time": self.next_funding_time.isoformat(),
            "annualized_rate": self.annualized_rate,
            "rate_percentage": self.rate_percentage,
            "annualized_percentage": self.annualized_percentage
        }


@dataclass
class OpenInterest:
    """未平仓合约数据"""
    symbol: str
    timestamp: datetime
    open_interest: float  # 未平仓合约数量
    open_interest_usd: float  # 未平仓合约价值(USD)
    price: float

    # 计算
    oi_change_24h: float = field(init=False)
    oi_change_percentage: float = field(init=False)

    def __post_init__(self):
        """初始化后计算 (需要历史数据支持)"""
        # 这里需要历史数据来计算24小时变化
        self.oi_change_24h = 0.0  # 实际应用中需要从历史数据计算
        self.oi_change_percentage = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open_interest": self.open_interest,
            "open_interest_usd": self.open_interest_usd,
            "price": self.price,
            "oi_change_24h": self.oi_change_24h,
            "oi_change_percentage": self.oi_change_percentage
        }


@dataclass
class MarketData:
    """综合市场数据"""
    symbol: str
    timestamp: datetime

    # 主要数据
    ohlcv: Optional[OHLCV] = field(default=None)
    ticker: Optional[Ticker] = field(default=None)
    orderbook: Optional[OrderBook] = field(default=None)
    trades: List[Trade] = field(default_factory=list)
    liquidity: Optional[LiquidityData] = field(default=None)
    funding_rate: Optional[FundingRate] = field(default=None)
    open_interest: Optional[OpenInterest] = field(default=None)

    # 市场条件
    volatility: float = field(default=0.0)  # 波动率
    trend_strength: float = field(default=0.0)  # 趋势强度 (-1到1)
    market_sentiment: float = field(default=0.0)  # 市场情绪 (-1到1)

    # 质量指标
    data_quality_score: float = field(default=1.0)  # 数据质量评分 (0-1)
    completeness_score: float = field(default=1.0)  # 完整性评分 (0-1)
    timeliness_score: float = field(default=1.0)  # 及时性评分 (0-1)

    @property
    def current_price(self) -> Optional[float]:
        """当前价格"""
        if self.ohlcv:
            return self.ohlcv.close
        elif self.ticker:
            return self.ticker.last_price
        elif self.orderbook and self.orderbook.mid_price:
            return self.orderbook.mid_price
        return None

    @property
    def is_complete(self) -> bool:
        """检查数据完整性"""
        required_fields = ['symbol', 'timestamp', 'current_price']
        return all(getattr(self, field) is not None for field in required_fields)

    @property
    def overall_quality_score(self) -> float:
        """综合质量评分"""
        scores = [
            self.data_quality_score,
            self.completeness_score,
            self.timeliness_score
        ]
        return sum(scores) / len(scores)

    def validate_data(self) -> List[str]:
        """验证数据质量"""
        errors = []

        if not self.symbol:
            errors.append("交易对符号不能为空")

        if self.current_price is None:
            errors.append("缺少价格数据")

        if self.overall_quality_score < 0.7:
            errors.append("数据质量评分过低")

        if not self.is_complete:
            errors.append("数据不完整")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "ohlcv": self.ohlcv.to_dict() if self.ohlcv else None,
            "ticker": self.ticker.to_dict() if self.ticker else None,
            "orderbook": self.orderbook.to_dict() if self.orderbook else None,
            "trades": [trade.to_dict() for trade in self.trades],
            "liquidity": self.liquidity.to_dict() if self.liquidity else None,
            "funding_rate": self.funding_rate.to_dict() if self.funding_rate else None,
            "open_interest": self.open_interest.to_dict() if self.open_interest else None,
            "current_price": self.current_price,
            "volatility": self.volatility,
            "trend_strength": self.trend_strength,
            "market_sentiment": self.market_sentiment,
            "data_quality_score": self.data_quality_score,
            "completeness_score": self.completeness_score,
            "timeliness_score": self.timeliness_score,
            "overall_quality_score": self.overall_quality_score
        }

    @classmethod
    def from_ohlcv(cls, ohlcv: OHLCV) -> 'MarketData':
        """从OHLCV创建市场数据"""
        return cls(
            symbol=ohlcv.symbol,
            timestamp=ohlcv.timestamp,
            ohlcv=ohlcv,
            current_price=ohlcv.close
        )

    @classmethod
    def from_ticker(cls, ticker: Ticker) -> 'MarketData':
        """从Ticker创建市场数据"""
        return cls(
            symbol=ticker.symbol,
            timestamp=ticker.timestamp,
            ticker=ticker,
            current_price=ticker.last_price
        )


def create_market_data_dataframe(data_list: List[MarketData]) -> pd.DataFrame:
    """创建市场数据DataFrame"""
    if not data_list:
        return pd.DataFrame()

    records = []
    for data in data_list:
        record = {
            "symbol": data.symbol,
            "timestamp": data.timestamp,
            "current_price": data.current_price,
            "volatility": data.volatility,
            "trend_strength": data.trend_strength,
            "market_sentiment": data.market_sentiment,
            "data_quality_score": data.data_quality_score,
            "completeness_score": data.completeness_score,
            "timeliness_score": data.timeliness_score,
            "overall_quality_score": data.overall_quality_score
        }

        if data.ohlcv:
            record.update({
                "open": data.ohlcv.open,
                "high": data.ohlcv.high,
                "low": data.ohlcv.low,
                "close": data.ohlcv.close,
                "volume": data.ohlcv.volume,
                "timeframe": data.ohlcv.timeframe.value
            })

        if data.ticker:
            record.update({
                "bid_price": data.ticker.bid_price,
                "ask_price": data.ticker.ask_price,
                "spread": data.ticker.spread,
                "liquidity_score": data.ticker.liquidity_score
            })

        records.append(record)

    return pd.DataFrame(records)
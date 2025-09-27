"""
数据接收与处理模块

该模块负责接收、验证、处理和标准化来自多个数据源的实时市场数据，
为做空分析提供高质量的数据输入。
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

from ..models.market_data import (
    MarketData,
    OHLCV,
    Ticker,
    OrderBook,
    OrderBookLevel,
    Trade,
    LiquidityData,
    FundingRate,
    OpenInterest,
    MarketDataType,
    TimeFrame
)
from ..models.short_signal import ShortSignal
from ..config import get_core_config
from ..utils.performance_monitor import PerformanceMonitor


class DataSource(Enum):
    """数据源类型"""
    EXCHANGE_API = "exchange_api"        # 交易所API
    WEBSOCKET = "websocket"              # WebSocket实时数据
    DATABASE = "database"                # 数据库历史数据
    EXTERNAL_API = "external_api"        # 外部API
    FILE = "file"                        # 文件数据


class DataQuality(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 优秀 (0.9-1.0)
    GOOD = "good"           # 良好 (0.7-0.9)
    FAIR = "fair"           # 一般 (0.5-0.7)
    POOR = "poor"           # 较差 (0.3-0.5)
    UNUSABLE = "unusable"   # 不可用 (<0.3)


class ProcessingStatus(Enum):
    """数据处理状态"""
    RECEIVED = "received"     # 已接收
    VALIDATED = "validated"   # 已验证
    PROCESSED = "processed"   # 已处理
    ENRICHED = "enriched"     # 已增强
    STORED = "stored"         # 已存储
    FAILED = "failed"         # 失败


@dataclass
class DataStream:
    """数据流信息"""
    stream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: DataSource = field()
    symbol: str = field()
    data_type: MarketDataType = field()
    status: ProcessingStatus = field(default=ProcessingStatus.RECEIVED)

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    received_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = field(default=None)

    # 数据内容
    raw_data: Dict[str, Any] = field(default_factory=dict)
    processed_data: Optional[MarketData] = field(default=None)

    # 质量指标
    quality_score: float = field(default=1.0)
    completeness_score: float = field(default=1.0)
    timeliness_score: float = field(default=1.0)

    # 错误信息
    error_message: Optional[str] = field(default=None)
    warnings: List[str] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingMetrics:
    """处理指标统计"""
    total_processed: int = field(default=0)
    success_count: int = field(default=0)
    failure_count: int = field(default=0)
    average_processing_time_ms: float = field(default=0.0)
    data_quality_scores: List[float] = field(default_factory=list)

    # 按数据源统计
    source_stats: Dict[DataSource, Dict[str, int]] = field(default_factory=dict)

    # 按数据类型统计
    type_stats: Dict[MarketDataType, Dict[str, int]] = field(default_factory=dict)

    def update_metrics(self, stream: DataStream, processing_time_ms: float):
        """更新处理指标"""
        self.total_processed += 1

        if stream.status == ProcessingStatus.FAILED:
            self.failure_count += 1
        else:
            self.success_count += 1

        # 更新处理时间
        self.average_processing_time_ms = (
            (self.average_processing_time_ms * (self.total_processed - 1) + processing_time_ms)
            / self.total_processed
        )

        # 更新质量分数
        overall_score = (stream.quality_score + stream.completeness_score + stream.timeliness_score) / 3
        self.data_quality_scores.append(overall_score)

        # 保持最近1000个质量分数
        if len(self.data_quality_scores) > 1000:
            self.data_quality_scores = self.data_quality_scores[-1000:]

        # 更新源统计
        if stream.source not in self.source_stats:
            self.source_stats[stream.source] = {"total": 0, "success": 0, "failed": 0}

        self.source_stats[stream.source]["total"] += 1
        if stream.status == ProcessingStatus.FAILED:
            self.source_stats[stream.source]["failed"] += 1
        else:
            self.source_stats[stream.source]["success"] += 1

        # 更新类型统计
        if stream.data_type not in self.type_stats:
            self.type_stats[stream.data_type] = {"total": 0, "success": 0, "failed": 0}

        self.type_stats[stream.data_type]["total"] += 1
        if stream.status == ProcessingStatus.FAILED:
            self.type_stats[stream.data_type]["failed"] += 1
        else:
            self.type_stats[stream.data_type]["success"] += 1

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_processed == 0:
            return 0.0
        return self.success_count / self.total_processed

    def get_average_quality_score(self) -> float:
        """获取平均质量分数"""
        if not self.data_quality_scores:
            return 0.0
        return sum(self.data_quality_scores) / len(self.data_quality_scores)


class DataValidator:
    """数据验证器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_raw_data(self, raw_data: Dict[str, Any], data_type: MarketDataType) -> List[str]:
        """
        验证原始数据

        Args:
            raw_data: 原始数据字典
            data_type: 数据类型

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        try:
            # 基础字段验证
            if "symbol" not in raw_data or not raw_data["symbol"]:
                errors.append("缺少或无效的symbol字段")

            if "timestamp" not in raw_data:
                errors.append("缺少timestamp字段")
            else:
                try:
                    timestamp = self._parse_timestamp(raw_data["timestamp"])
                    if timestamp > datetime.now() + timedelta(minutes=5):
                        errors.append("timestamp时间过于超前")
                    elif timestamp < datetime.now() - timedelta(days=1):
                        errors.append("timestamp时间过于陈旧")
                except Exception:
                    errors.append("timestamp格式无效")

            # 根据数据类型进行特定验证
            if data_type == MarketDataType.OHLCV:
                errors.extend(self._validate_ohlcv_data(raw_data))
            elif data_type == MarketDataType.TICKER:
                errors.extend(self._validate_ticker_data(raw_data))
            elif data_type == MarketDataType.ORDERBOOK:
                errors.extend(self._validate_orderbook_data(raw_data))
            elif data_type == MarketDataType.TRADES:
                errors.extend(self._validate_trades_data(raw_data))

        except Exception as e:
            errors.append(f"数据验证异常: {str(e)}")

        return errors

    def _validate_ohlcv_data(self, data: Dict[str, Any]) -> List[str]:
        """验证OHLCV数据"""
        errors = []

        required_fields = ["open", "high", "low", "close", "volume"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少{field}字段")
            elif not isinstance(data[field], (int, float)) or data[field] <= 0:
                errors.append(f"{field}必须是正数")

        # 价格逻辑验证
        if all(field in data for field in ["open", "high", "low", "close"]):
            if data["high"] < max(data["open"], data["close"]):
                errors.append("high价格小于open或close")
            if data["low"] > min(data["open"], data["close"]):
                errors.append("low价格大于open或close")

        return errors

    def _validate_ticker_data(self, data: Dict[str, Any]) -> List[str]:
        """验证行情数据"""
        errors = []

        required_fields = ["last_price", "bid_price", "ask_price"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少{field}字段")
            elif not isinstance(data[field], (int, float)) or data[field] <= 0:
                errors.append(f"{field}必须是正数")

        # 价格逻辑验证
        if all(field in data for field in ["bid_price", "ask_price"]):
            if data["bid_price"] >= data["ask_price"]:
                errors.append("bid_price必须小于ask_price")

        return errors

    def _validate_orderbook_data(self, data: Dict[str, Any]) -> List[str]:
        """验证订单簿数据"""
        errors = []

        if "bids" not in data or not isinstance(data["bids"], list):
            errors.append("缺少或无效的bids字段")
        else:
            for i, bid in enumerate(data["bids"][:5]):  # 只验证前5个
                if not isinstance(bid, (list, dict)) or len(bid) < 2:
                    errors.append(f"bids[{i}]格式无效")
                elif isinstance(bid, list) and (bid[0] <= 0 or bid[1] <= 0):
                    errors.append(f"bids[{i}]价格和数量必须为正数")

        if "asks" not in data or not isinstance(data["asks"], list):
            errors.append("缺少或无效的asks字段")
        else:
            for i, ask in enumerate(data["asks"][:5]):  # 只验证前5个
                if not isinstance(ask, (list, dict)) or len(ask) < 2:
                    errors.append(f"asks[{i}]格式无效")
                elif isinstance(ask, list) and (ask[0] <= 0 or ask[1] <= 0):
                    errors.append(f"asks[{i}]价格和数量必须为正数")

        return errors

    def _validate_trades_data(self, data: Dict[str, Any]) -> List[str]:
        """验证交易数据"""
        errors = []

        required_fields = ["price", "volume", "side"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少{field}字段")

        if "price" in data and (not isinstance(data["price"], (int, float)) or data["price"] <= 0):
            errors.append("price必须是正数")

        if "volume" in data and (not isinstance(data["volume"], (int, float)) or data["volume"] <= 0):
            errors.append("volume必须是正数")

        if "side" in data and data["side"] not in ["buy", "sell"]:
            errors.append("side必须是'buy'或'sell'")

        return errors

    def _parse_timestamp(self, timestamp: Union[str, int, float, datetime]) -> datetime:
        """解析时间戳"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            # 处理毫秒级时间戳
            if timestamp > 1e12:  # 毫秒时间戳
                return datetime.fromtimestamp(timestamp / 1000)
            else:  # 秒级时间戳
                return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            # 尝试解析ISO格式
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                # 尝试其他格式
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f"
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"无法解析时间戳格式: {timestamp}")
        else:
            raise ValueError(f"不支持的时间戳类型: {type(timestamp)}")


class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()

    def process_raw_data(self, stream: DataStream) -> DataStream:
        """
        处理原始数据

        Args:
            stream: 数据流对象

        Returns:
            DataStream: 处理后的数据流对象
        """
        start_time = time.time()

        try:
            # 验证数据
            validation_errors = self.validator.validate_raw_data(
                stream.raw_data, stream.data_type
            )

            if validation_errors:
                stream.status = ProcessingStatus.FAILED
                stream.error_message = f"数据验证失败: {'; '.join(validation_errors)}"
                stream.quality_score = 0.0
                stream.processed_at = datetime.now()
                return stream

            stream.status = ProcessingStatus.VALIDATED

            # 根据数据类型进行处理
            if stream.data_type == MarketDataType.OHLCV:
                processed_data = self._process_ohlcv(stream.raw_data)
            elif stream.data_type == MarketDataType.TICKER:
                processed_data = self._process_ticker(stream.raw_data)
            elif stream.data_type == MarketDataType.ORDERBOOK:
                processed_data = self._process_orderbook(stream.raw_data)
            elif stream.data_type == MarketDataType.TRADES:
                processed_data = self._process_trades(stream.raw_data)
            else:
                raise ValueError(f"不支持的数据类型: {stream.data_type}")

            # 增强数据
            enriched_data = self._enrich_market_data(processed_data, stream)

            # 设置处理后的数据
            stream.processed_data = enriched_data
            stream.status = ProcessingStatus.PROCESSED

            # 计算质量分数
            stream.quality_score = self._calculate_quality_score(stream)
            stream.completeness_score = self._calculate_completeness_score(stream)
            stream.timeliness_score = self._calculate_timeliness_score(stream)

            stream.processed_at = datetime.now()

        except Exception as e:
            stream.status = ProcessingStatus.FAILED
            stream.error_message = f"数据处理失败: {str(e)}"
            stream.processed_at = datetime.now()
            self.logger.error(f"数据处理失败: {e}")

        processing_time_ms = (time.time() - start_time) * 1000
        stream.metadata["processing_time_ms"] = processing_time_ms

        return stream

    def _process_ohlcv(self, raw_data: Dict[str, Any]) -> OHLCV:
        """处理OHLCV数据"""
        return OHLCV(
            symbol=raw_data["symbol"],
            timestamp=self.validator._parse_timestamp(raw_data["timestamp"]),
            open=float(raw_data["open"]),
            high=float(raw_data["high"]),
            low=float(raw_data["low"]),
            close=float(raw_data["close"]),
            volume=float(raw_data["volume"]),
            timeframe=TimeFrame(raw_data.get("timeframe", "1h")),
            quote_volume=float(raw_data.get("quote_volume", 0)),
            trade_count=int(raw_data.get("trade_count", 0)),
            taker_buy_volume=float(raw_data.get("taker_buy_volume", 0)),
            taker_buy_quote_volume=float(raw_data.get("taker_buy_quote_volume", 0))
        )

    def _process_ticker(self, raw_data: Dict[str, Any]) -> Ticker:
        """处理行情数据"""
        return Ticker(
            symbol=raw_data["symbol"],
            timestamp=self.validator._parse_timestamp(raw_data["timestamp"]),
            last_price=float(raw_data["last_price"]),
            bid_price=float(raw_data["bid_price"]),
            ask_price=float(raw_data["ask_price"]),
            bid_volume=float(raw_data.get("bid_volume", 0)),
            ask_volume=float(raw_data.get("ask_volume", 0))
        )

    def _process_orderbook(self, raw_data: Dict[str, Any]) -> OrderBook:
        """处理订单簿数据"""
        bids = []
        asks = []

        # 处理买单
        for bid_data in raw_data["bids"][:20]:  # 只取前20层
            if isinstance(bid_data, list):
                bids.append(OrderBookLevel(
                    price=float(bid_data[0]),
                    volume=float(bid_data[1])
                ))
            elif isinstance(bid_data, dict):
                bids.append(OrderBookLevel(
                    price=float(bid_data["price"]),
                    volume=float(bid_data["volume"])
                ))

        # 处理卖单
        for ask_data in raw_data["asks"][:20]:  # 只取前20层
            if isinstance(ask_data, list):
                asks.append(OrderBookLevel(
                    price=float(ask_data[0]),
                    volume=float(ask_data[1])
                ))
            elif isinstance(ask_data, dict):
                asks.append(OrderBookLevel(
                    price=float(ask_data["price"]),
                    volume=float(ask_data["volume"])
                ))

        return OrderBook(
            symbol=raw_data["symbol"],
            timestamp=self.validator._parse_timestamp(raw_data["timestamp"]),
            bids=bids,
            asks=asks
        )

    def _process_trades(self, raw_data: Dict[str, Any]) -> Trade:
        """处理交易数据"""
        return Trade(
            symbol=raw_data["symbol"],
            timestamp=self.validator._parse_timestamp(raw_data["timestamp"]),
            price=float(raw_data["price"]),
            volume=float(raw_data["volume"]),
            side=raw_data["side"],
            trade_id=raw_data.get("trade_id"),
            order_id=raw_data.get("order_id"),
            fee=float(raw_data.get("fee", 0)),
            fee_currency=raw_data.get("fee_currency")
        )

    def _enrich_market_data(self, data: Union[OHLCV, Ticker, OrderBook, Trade], stream: DataStream) -> MarketData:
        """增强市场数据"""
        market_data = MarketData(
            symbol=data.symbol,
            timestamp=data.timestamp
        )

        # 根据数据类型设置相应字段
        if isinstance(data, OHLCV):
            market_data.ohlcv = data
            market_data.current_price = data.close
        elif isinstance(data, Ticker):
            market_data.ticker = data
            market_data.current_price = data.last_price
        elif isinstance(data, OrderBook):
            market_data.orderbook = data
            market_data.current_price = data.mid_price
        elif isinstance(data, Trade):
            market_data.trades.append(data)
            market_data.current_price = data.price

        # 添加元数据
        market_data.metadata = {
            "source": stream.source.value,
            "stream_id": stream.stream_id,
            "received_at": stream.received_at.isoformat(),
            "processing_time_ms": stream.metadata.get("processing_time_ms", 0)
        }

        return market_data

    def _calculate_quality_score(self, stream: DataStream) -> float:
        """计算数据质量分数"""
        if stream.status == ProcessingStatus.FAILED:
            return 0.0

        # 基础质量分数
        quality_score = 1.0

        # 根据数据类型调整
        if stream.data_type == MarketDataType.OHLCV:
            # OHLCV数据质量评估
            ohlcv = stream.processed_data.ohlcv
            if ohlcv:
                # 检查价格逻辑
                if ohlcv.high < max(ohlcv.open, ohlcv.close):
                    quality_score -= 0.2
                if ohlcv.low > min(ohlcv.open, ohlcv.close):
                    quality_score -= 0.2
                # 检查数据合理性
                if ohlcv.volume == 0:
                    quality_score -= 0.1

        elif stream.data_type == MarketDataType.TICKER:
            # Ticker数据质量评估
            ticker = stream.processed_data.ticker
            if ticker:
                # 检查价差
                spread_percentage = ticker.spread_percentage
                if spread_percentage > 1.0:  # 价差超过1%
                    quality_score -= 0.3
                elif spread_percentage > 0.5:  # 价差超过0.5%
                    quality_score -= 0.1

        return max(0.0, quality_score)

    def _calculate_completeness_score(self, stream: DataStream) -> float:
        """计算数据完整性分数"""
        if stream.status == ProcessingStatus.FAILED:
            return 0.0

        completeness = 1.0

        # 检查字段完整性
        required_fields_map = {
            MarketDataType.OHLCV: ["open", "high", "low", "close", "volume"],
            MarketDataType.TICKER: ["last_price", "bid_price", "ask_price"],
            MarketDataType.ORDERBOOK: ["bids", "asks"],
            MarketDataType.TRADES: ["price", "volume", "side"]
        }

        required_fields = required_fields_map.get(stream.data_type, [])
        if required_fields:
            missing_fields = [field for field in required_fields if field not in stream.raw_data]
            if missing_fields:
                completeness -= len(missing_fields) * 0.2

        return max(0.0, completeness)

    def _calculate_timeliness_score(self, stream: DataStream) -> float:
        """计算数据及时性分数"""
        if stream.status == ProcessingStatus.FAILED:
            return 0.0

        # 计算数据延迟
        data_timestamp = stream.processed_data.timestamp
        current_time = datetime.now()
        delay_seconds = (current_time - data_timestamp).total_seconds()

        # 根据延迟程度评分
        if delay_seconds < 1:  # 1秒内
            return 1.0
        elif delay_seconds < 5:  # 5秒内
            return 0.9
        elif delay_seconds < 30:  # 30秒内
            return 0.7
        elif delay_seconds < 60:  # 1分钟内
            return 0.5
        elif delay_seconds < 300:  # 5分钟内
            return 0.3
        else:
            return 0.1


class DataReceiver:
    """数据接收器"""

    def __init__(self, config=None):
        """
        初始化数据接收器

        Args:
            config: 配置对象
        """
        self.config = config or get_core_config()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # 核心组件
        self.validator = DataValidator()
        self.processor = DataProcessor()

        # 数据流管理
        self.active_streams: Dict[str, DataStream] = {}
        self.processing_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()

        # 处理指标
        self.metrics = ProcessingMetrics()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_requests)

        # 运行状态
        self._is_running = False
        self._processing_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动数据接收器"""
        if self._is_running:
            self.logger.warning("数据接收器已在运行中")
            return

        try:
            self._is_running = True
            self._processing_task = asyncio.create_task(self._process_data_streams())

            self.logger.info("数据接收器启动成功")

        except Exception as e:
            self.logger.error(f"数据接收器启动失败: {e}")
            raise

    async def stop(self):
        """停止数据接收器"""
        if not self._is_running:
            return

        try:
            self._is_running = False

            # 停止处理任务
            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass

            # 关闭线程池
            self.executor.shutdown(wait=True)

            self.logger.info("数据接收器已停止")

        except Exception as e:
            self.logger.error(f"数据接收器停止失败: {e}")

    async def receive_data(
        self,
        raw_data: Dict[str, Any],
        data_type: MarketDataType,
        source: DataSource,
        symbol: str
    ) -> str:
        """
        接收原始数据

        Args:
            raw_data: 原始数据
            data_type: 数据类型
            source: 数据源
            symbol: 交易对符号

        Returns:
            str: 数据流ID
        """
        # 创建数据流对象
        stream = DataStream(
            source=source,
            symbol=symbol,
            data_type=data_type,
            raw_data=raw_data,
            received_at=datetime.now()
        )

        # 添加到活动流
        self.active_streams[stream.stream_id] = stream

        # 加入处理队列
        await self.processing_queue.put(stream)

        self.logger.debug(f"接收数据: {symbol} - {data_type.value}")
        return stream.stream_id

    async def receive_ohlcv(
        self,
        symbol: str,
        timestamp: Union[str, int, datetime],
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        timeframe: str = "1h",
        source: DataSource = DataSource.EXCHANGE_API
    ) -> str:
        """接收OHLCV数据的便捷方法"""
        raw_data = {
            "symbol": symbol,
            "timestamp": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "timeframe": timeframe
        }

        return await self.receive_data(
            raw_data, MarketDataType.OHLCV, source, symbol
        )

    async def receive_ticker(
        self,
        symbol: str,
        timestamp: Union[str, int, datetime],
        last_price: float,
        bid_price: float,
        ask_price: float,
        bid_volume: float = 0,
        ask_volume: float = 0,
        source: DataSource = DataSource.EXCHANGE_API
    ) -> str:
        """接收行情数据的便捷方法"""
        raw_data = {
            "symbol": symbol,
            "timestamp": timestamp,
            "last_price": last_price,
            "bid_price": bid_price,
            "ask_price": ask_price,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume
        }

        return await self.receive_data(
            raw_data, MarketDataType.TICKER, source, symbol
        )

    async def receive_orderbook(
        self,
        symbol: str,
        timestamp: Union[str, int, datetime],
        bids: List[List[float]],
        asks: List[List[float]],
        source: DataSource = DataSource.WEBSOCKET
    ) -> str:
        """接收订单簿数据的便捷方法"""
        raw_data = {
            "symbol": symbol,
            "timestamp": timestamp,
            "bids": bids,
            "asks": asks
        }

        return await self.receive_data(
            raw_data, MarketDataType.ORDERBOOK, source, symbol
        )

    async def _process_data_streams(self):
        """处理数据流的主循环"""
        while self._is_running:
            try:
                # 从队列获取数据流
                stream = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._get_stream_with_timeout
                )

                if stream is None:
                    continue

                # 处理数据
                processed_stream = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.processor.process_raw_data, stream
                )

                # 更新指标
                processing_time = processed_stream.metadata.get("processing_time_ms", 0)
                self.metrics.update_metrics(processed_stream, processing_time)

                # 加入输出队列
                await self.output_queue.put(processed_stream)

                # 记录处理结果
                if processed_stream.status == ProcessingStatus.FAILED:
                    self.logger.warning(f"数据处理失败: {processed_stream.error_message}")
                else:
                    self.logger.debug(f"数据处理成功: {processed_stream.symbol}")

                # 清理已完成的数据流
                if processed_stream.stream_id in self.active_streams:
                    del self.active_streams[processed_stream.stream_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"数据处理异常: {e}")
                await asyncio.sleep(1)

    def _get_stream_with_timeout(self, timeout: float = 1.0) -> Optional[DataStream]:
        """带超时获取数据流"""
        try:
            return self.processing_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    async def get_processed_data(self, timeout: float = 5.0) -> Optional[DataStream]:
        """
        获取处理后的数据

        Args:
            timeout: 超时时间

        Returns:
            DataStream: 处理后的数据流
        """
        try:
            return await asyncio.wait_for(self.output_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def validate_and_preprocess(self, market_data: MarketData) -> MarketData:
        """
        验证和预处理市场数据

        Args:
            market_data: 市场数据

        Returns:
            MarketData: 验证和预处理后的市场数据
        """
        try:
            with self.performance_monitor.measure_latency("data_validation"):
                # 验证数据完整性
                validation_errors = market_data.validate_data()

                if validation_errors:
                    self.logger.warning(f"市场数据验证失败: {validation_errors}")
                    # 设置低质量分数
                    market_data.data_quality_score = 0.3
                else:
                    # 增强数据质量
                    market_data = self._enhance_market_data(market_data)

                return market_data

        except Exception as e:
            self.logger.error(f"市场数据预处理失败: {e}")
            return market_data

    def _enhance_market_data(self, market_data: MarketData) -> MarketData:
        """增强市场数据"""
        # 计算技术指标
        if market_data.ohlcv:
            self._calculate_technical_indicators(market_data)

        # 计算市场情绪
        self._calculate_market_sentiment(market_data)

        # 评估流动性
        self._assess_liquidity(market_data)

        return market_data

    def _calculate_technical_indicators(self, market_data: MarketData):
        """计算技术指标"""
        ohlcv = market_data.ohlcv
        if not ohlcv:
            return

        # 计算价格变化
        price_change = ohlcv.close - ohlcv.open
        price_change_pct = (price_change / ohlcv.open) * 100 if ohlcv.open > 0 else 0

        # 计算波动率
        volatility = (ohlcv.high - ohlcv.low) / ohlcv.close if ohlcv.close > 0 else 0

        # 更新市场数据
        market_data.volatility = volatility
        market_data.metadata.update({
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "price_range": ohlcv.high - ohlcv.low,
            "body_size": abs(ohlcv.close - ohlcv.open),
            "is_green": ohlcv.close > ohlcv.open,
            "is_doji": abs(ohlcv.close - ohlcv.open) / (ohlcv.high - ohlcv.low) < 0.1 if ohlcv.high > ohlcv.low else False
        })

    def _calculate_market_sentiment(self, market_data: MarketData):
        """计算市场情绪"""
        sentiment = 0.0

        # 基于价格变化
        if "price_change_pct" in market_data.metadata:
            price_change_pct = market_data.metadata["price_change_pct"]
            if price_change_pct > 5:  # 大涨
                sentiment = 0.8
            elif price_change_pct > 2:  # 中涨
                sentiment = 0.5
            elif price_change_pct < -5:  # 大跌
                sentiment = -0.8
            elif price_change_pct < -2:  # 中跌
                sentiment = -0.5

        market_data.market_sentiment = sentiment

    def _assess_liquidity(self, market_data: MarketData):
        """评估流动性"""
        liquidity_score = 0.5  # 默认中等流动性

        if market_data.ticker:
            # 基于价差评估流动性
            spread_percentage = market_data.ticker.spread_percentage
            if spread_percentage < 0.1:
                liquidity_score = 0.9
            elif spread_percentage < 0.5:
                liquidity_score = 0.7
            elif spread_percentage < 1.0:
                liquidity_score = 0.5
            else:
                liquidity_score = 0.3

        elif market_data.orderbook:
            # 基于订单簿深度评估流动性
            liquidity_score = market_data.orderbook.calculate_liquidity_score()

        market_data.metadata["liquidity_score"] = liquidity_score

    def get_status(self) -> Dict[str, Any]:
        """获取数据接收器状态"""
        return {
            "is_running": self._is_running,
            "active_streams": len(self.active_streams),
            "processing_queue_size": self.processing_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "metrics": {
                "total_processed": self.metrics.total_processed,
                "success_rate": self.metrics.get_success_rate(),
                "average_quality_score": self.metrics.get_average_quality_score(),
                "average_processing_time_ms": self.metrics.average_processing_time_ms
            },
            "performance_metrics": self.performance_monitor.get_metrics()
        }

    def health_check(self) -> bool:
        """健康检查"""
        return (
            self._is_running and
            self.metrics.get_success_rate() > 0.8 and
            self.metrics.get_average_quality_score() > 0.7
        )


# 工具函数
def create_data_stream_from_dict(data: Dict[str, Any]) -> DataStream:
    """从字典创建数据流"""
    return DataStream(
        source=DataSource(data.get("source", "exchange_api")),
        symbol=data["symbol"],
        data_type=MarketDataType(data["data_type"]),
        raw_data=data.get("raw_data", {}),
        metadata=data.get("metadata", {})
    )


def validate_market_data_completeness(market_data: MarketData) -> List[str]:
    """验证市场数据完整性"""
    errors = []

    if not market_data.symbol:
        errors.append("交易对符号不能为空")

    if not market_data.current_price:
        errors.append("当前价格不能为空")

    if market_data.overall_quality_score < 0.5:
        errors.append("数据质量评分过低")

    return errors
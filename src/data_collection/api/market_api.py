"""
Market data API endpoints for the data collection agent.

This module provides RESTful API endpoints for accessing market data,
including OHLCV data, order book data, trade data, and ticker data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ..core.data_collector import DataCollector
from ..core.exchange_manager import ExchangeManager
from ..models.market_data import OHLCVData, OrderBookData, TradeData, TickerData
from ..models.database import get_timescaledb_session
from ..utils.helpers import format_timestamp, normalize_symbol


# Pydantic models for API requests/responses
class OHLCVRequest(BaseModel):
    exchange: str = Field(..., description="Exchange name")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field("1h", description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    limit: int = Field(100, description="Maximum number of records", ge=1, le=1000)


class OrderBookRequest(BaseModel):
    exchange: str = Field(..., description="Exchange name")
    symbol: str = Field(..., description="Trading symbol")
    depth: int = Field(20, description="Order book depth", ge=1, le=100)


class TradesRequest(BaseModel):
    exchange: str = Field(..., description="Exchange name")
    symbol: str = Field(..., description="Trading symbol")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    limit: int = Field(100, description="Maximum number of records", ge=1, le=1000)


class TickerRequest(BaseModel):
    exchange: str = Field(..., description="Exchange name")
    symbol: str = Field(..., description="Trading symbol")


class OHLCVResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    exchange: str
    symbol: str
    timeframe: str


class OrderBookResponse(BaseModel):
    timestamp: datetime
    bids: List[List[float]]
    asks: List[List[float]]
    best_bid: float
    best_ask: float
    spread: float
    spread_percent: float
    mid_price: float
    exchange: str
    symbol: str


class TradeResponse(BaseModel):
    timestamp: datetime
    price: float
    amount: float
    side: str
    exchange: str
    symbol: str
    trade_id: Optional[str] = None


class TickerResponse(BaseModel):
    timestamp: datetime
    last: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    exchange: str
    symbol: str


class MarketStatsResponse(BaseModel):
    total_records: int
    exchanges_count: int
    symbols_count: int
    latest_timestamp: Optional[datetime]
    data_types: List[str]


# Create router
market_router = APIRouter(prefix="/api/v1/market", tags=["market-data"])

# Initialize dependencies
data_collector = None
exchange_manager = None


def get_data_collector():
    """Get data collector instance."""
    global data_collector
    if data_collector is None:
        data_collector = DataCollector()
    return data_collector


def get_exchange_manager():
    """Get exchange manager instance."""
    global exchange_manager
    if exchange_manager is None:
        exchange_manager = ExchangeManager()
    return exchange_manager


@market_router.get("/exchanges", response_model=List[str])
async def get_exchanges():
    """Get list of available exchanges."""
    manager = get_exchange_manager()
    try:
        exchanges = await manager.get_all_exchanges()
        return exchanges
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get exchanges: {str(e)}")


@market_router.get("/exchanges/{exchange}/symbols", response_model=List[str])
async def get_exchange_symbols(exchange: str):
    """Get list of available symbols for an exchange."""
    manager = get_exchange_manager()
    try:
        markets = await manager.get_markets(exchange)
        symbols = [market['symbol'] for market in markets if market.get('active', False)]
        return symbols[:100]  # Limit to 100 symbols
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get symbols for {exchange}: {str(e)}")


@market_router.post("/ohlcv", response_model=List[OHLCVResponse])
async def get_ohlcv_data(request: OHLCVRequest):
    """Get OHLCV data."""
    session = get_timescaledb_session()

    try:
        # Build query
        query = session.query(OHLCVData).filter(
            OHLCVData.exchange == request.exchange,
            OHLCVData.symbol == normalize_symbol(request.symbol, request.exchange),
            OHLCVData.timeframe == request.timeframe
        )

        # Apply time filters
        if request.start_time:
            query = query.filter(OHLCVData.timestamp >= request.start_time)
        if request.end_time:
            query = query.filter(OHLCVData.timestamp <= request.end_time)

        # Apply limit and order
        query = query.order_by(OHLCVData.timestamp.desc()).limit(request.limit)

        # Execute query
        ohlcv_records = query.all()
        session.close()

        # Convert to response format
        return [
            OHLCVResponse(
                timestamp=record.timestamp,
                open=record.open,
                high=record.high,
                low=record.low,
                close=record.close,
                volume=record.volume,
                exchange=record.exchange,
                symbol=record.symbol,
                timeframe=record.timeframe
            )
            for record in ohlcv_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get OHLCV data: {str(e)}")


@market_router.get("/ohlcv/latest", response_model=List[OHLCVResponse])
async def get_latest_ohlcv(
    exchange: str = Query(..., description="Exchange name"),
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
    limit: int = Query(10, description="Number of latest records", ge=1, le=100)
):
    """Get latest OHLCV data."""
    session = get_timescaledb_session()

    try:
        # Get latest records
        ohlcv_records = OHLCVData.get_latest(
            session, exchange, normalize_symbol(symbol, exchange), limit
        )
        session.close()

        # Convert to response format
        return [
            OHLCVResponse(
                timestamp=record.timestamp,
                open=record.open,
                high=record.high,
                low=record.low,
                close=record.close,
                volume=record.volume,
                exchange=record.exchange,
                symbol=record.symbol,
                timeframe=record.timeframe
            )
            for record in ohlcv_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get latest OHLCV data: {str(e)}")


@market_router.post("/orderbook", response_model=OrderBookResponse)
async def get_orderbook_data(request: OrderBookRequest):
    """Get current order book data."""
    session = get_timescaledb_session()

    try:
        # Get latest order book
        orderbook_records = OrderBookData.get_latest(
            session, request.exchange, normalize_symbol(request.symbol, request.exchange), 1
        )
        session.close()

        if not orderbook_records:
            raise HTTPException(status_code=404, detail="No order book data found")

        orderbook = orderbook_records[0]

        return OrderBookResponse(
            timestamp=orderbook.timestamp,
            bids=orderbook.bids,
            asks=orderbook.asks,
            best_bid=orderbook.best_bid,
            best_ask=orderbook.best_ask,
            spread=orderbook.spread,
            spread_percent=orderbook.spread_percent,
            mid_price=orderbook.mid_price,
            exchange=orderbook.exchange,
            symbol=orderbook.symbol
        )

    except HTTPException:
        raise
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get order book data: {str(e)}")


@market_router.get("/orderbook/multi", response_model=Dict[str, OrderBookResponse])
async def get_multi_orderbook(
    exchange: str = Query(..., description="Exchange name"),
    symbols: str = Query(..., description="Comma-separated list of symbols")
):
    """Get order book data for multiple symbols."""
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    session = get_timescaledb_session()
    results = {}

    try:
        for symbol in symbol_list:
            try:
                orderbook_records = OrderBookData.get_latest(
                    session, exchange, normalize_symbol(symbol, exchange), 1
                )

                if orderbook_records:
                    orderbook = orderbook_records[0]
                    results[symbol] = OrderBookResponse(
                        timestamp=orderbook.timestamp,
                        bids=orderbook.bids,
                        asks=orderbook.asks,
                        best_bid=orderbook.best_bid,
                        best_ask=orderbook.best_ask,
                        spread=orderbook.spread,
                        spread_percent=orderbook.spread_percent,
                        mid_price=orderbook.mid_price,
                        exchange=orderbook.exchange,
                        symbol=orderbook.symbol
                    )
            except Exception as e:
                # Continue with other symbols if one fails
                continue

        session.close()
        return results

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get multi order book data: {str(e)}")


@market_router.post("/trades", response_model=List[TradeResponse])
async def get_trades_data(request: TradesRequest):
    """Get trades data."""
    session = get_timescaledb_session()

    try:
        # Build query
        query = session.query(TradeData).filter(
            TradeData.exchange == request.exchange,
            TradeData.symbol == normalize_symbol(request.symbol, request.exchange)
        )

        # Apply time filters
        if request.start_time:
            query = query.filter(TradeData.timestamp >= request.start_time)
        if request.end_time:
            query = query.filter(TradeData.timestamp <= request.end_time)

        # Apply limit and order
        query = query.order_by(TradeData.timestamp.desc()).limit(request.limit)

        # Execute query
        trade_records = query.all()
        session.close()

        # Convert to response format
        return [
            TradeResponse(
                timestamp=record.timestamp,
                price=record.price,
                amount=record.amount,
                side=record.side,
                exchange=record.exchange,
                symbol=record.symbol,
                trade_id=record.trade_id
            )
            for record in trade_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get trades data: {str(e)}")


@market_router.get("/trades/latest", response_model=List[TradeResponse])
async def get_latest_trades(
    exchange: str = Query(..., description="Exchange name"),
    symbol: str = Query(..., description="Trading symbol"),
    limit: int = Query(50, description="Number of latest trades", ge=1, le=1000)
):
    """Get latest trades data."""
    session = get_timescaledb_session()

    try:
        # Get latest trades
        trade_records = TradeData.get_latest(
            session, exchange, normalize_symbol(symbol, exchange), limit
        )
        session.close()

        # Convert to response format
        return [
            TradeResponse(
                timestamp=record.timestamp,
                price=record.price,
                amount=record.amount,
                side=record.side,
                exchange=record.exchange,
                symbol=record.symbol,
                trade_id=record.trade_id
            )
            for record in trade_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get latest trades data: {str(e)}")


@market_router.post("/ticker", response_model=TickerResponse)
async def get_ticker_data(request: TickerRequest):
    """Get current ticker data."""
    session = get_timescaledb_session()

    try:
        # Get latest ticker
        ticker_records = TickerData.get_latest(
            session, request.exchange, normalize_symbol(request.symbol, request.exchange), 1
        )
        session.close()

        if not ticker_records:
            raise HTTPException(status_code=404, detail="No ticker data found")

        ticker = ticker_records[0]

        return TickerResponse(
            timestamp=ticker.timestamp,
            last=ticker.last,
            bid=ticker.bid,
            ask=ticker.ask,
            high=ticker.high,
            low=ticker.low,
            volume=ticker.volume,
            change=ticker.change,
            change_percent=ticker.change_percent,
            exchange=ticker.exchange,
            symbol=ticker.symbol
        )

    except HTTPException:
        raise
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get ticker data: {str(e)}")


@market_router.get("/ticker/multi", response_model=Dict[str, TickerResponse])
async def get_multi_ticker(
    exchange: str = Query(..., description="Exchange name"),
    symbols: str = Query(..., description="Comma-separated list of symbols")
):
    """Get ticker data for multiple symbols."""
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")

    session = get_timescaledb_session()
    results = {}

    try:
        for symbol in symbol_list:
            try:
                ticker_records = TickerData.get_latest(
                    session, exchange, normalize_symbol(symbol, exchange), 1
                )

                if ticker_records:
                    ticker = ticker_records[0]
                    results[symbol] = TickerResponse(
                        timestamp=ticker.timestamp,
                        last=ticker.last,
                        bid=ticker.bid,
                        ask=ticker.ask,
                        high=ticker.high,
                        low=ticker.low,
                        volume=ticker.volume,
                        change=ticker.change,
                        change_percent=ticker.change_percent,
                        exchange=ticker.exchange,
                        symbol=ticker.symbol
                    )
            except Exception as e:
                # Continue with other symbols if one fails
                continue

        session.close()
        return results

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get multi ticker data: {str(e)}")


@market_router.get("/stats", response_model=MarketStatsResponse)
async def get_market_stats():
    """Get market data statistics."""
    session = get_timescaledb_session()

    try:
        # Count OHLCV records
        ohlcv_count = session.query(OHLCVData).count()

        # Count order book records
        orderbook_count = session.query(OrderBookData).count()

        # Count trade records
        trade_count = session.query(TradeData).count()

        # Count ticker records
        ticker_count = session.query(TickerData).count()

        total_records = ohlcv_count + orderbook_count + trade_count + ticker_count

        # Get unique exchanges and symbols
        exchanges = set()
        symbols = set()

        # Get from OHLCV data
        ohlcv_exchanges = session.query(OHLCVData.exchange).distinct().all()
        ohlcv_symbols = session.query(OHLCVData.symbol).distinct().all()
        exchanges.update(ex.exchange for ex in ohlcv_exchanges)
        symbols.update(sym.symbol for sym in ohlcv_symbols)

        # Get latest timestamp
        latest_timestamp = None
        try:
            latest_ohlcv = session.query(OHLCVData.timestamp).order_by(OHLCVData.timestamp.desc()).first()
            if latest_ohlcv:
                latest_timestamp = latest_ohlcv[0]
        except:
            pass

        session.close()

        return MarketStatsResponse(
            total_records=total_records,
            exchanges_count=len(exchanges),
            symbols_count=len(symbols),
            latest_timestamp=latest_timestamp,
            data_types=["ohlcv", "orderbook", "trades", "ticker"]
        )

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get market stats: {str(e)}")


@market_router.get("/timeframes", response_model=List[str])
async def get_available_timeframes():
    """Get available timeframes."""
    return ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]


@market_router.get("/collection/status")
async def get_collection_status():
    """Get data collection status."""
    collector = get_data_collector()
    try:
        status = collector.get_collection_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection status: {str(e)}")


@market_router.post("/collection/start")
async def start_collection():
    """Start data collection."""
    collector = get_data_collector()
    try:
        await collector.start()
        return {"status": "started", "message": "Data collection started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start collection: {str(e)}")


@market_router.post("/collection/stop")
async def stop_collection():
    """Stop data collection."""
    collector = get_data_collector()
    try:
        await collector.stop()
        return {"status": "stopped", "message": "Data collection stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop collection: {str(e)}")
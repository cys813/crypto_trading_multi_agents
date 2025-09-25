"""
Order data API endpoints for the data collection agent.

This module provides RESTful API endpoints for accessing order data,
including current orders, order history, and order statistics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ..core.order_manager import OrderManager
from ..models.order import Order, OrderHistory, OrderMetrics, OrderType, OrderSide, OrderStatus
from ..models.database import get_session
from ..utils.helpers import format_timestamp


# Pydantic models for API requests/responses
class OrderResponse(BaseModel):
    id: str
    exchange: str
    symbol: str
    order_id: str
    client_order_id: Optional[str] = None
    order_type: str
    side: str
    status: str
    price: Optional[float] = None
    amount: float
    filled_amount: float
    remaining_amount: Optional[float] = None
    cost: Optional[float] = None
    average_price: Optional[float] = None
    fee_cost: float
    fee_currency: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    fill_rate: float
    is_active: bool
    is_expired: bool


class OrderHistoryResponse(BaseModel):
    id: str
    order_id: str
    event_type: str
    event_timestamp: datetime
    status: Optional[str] = None
    filled_amount: float
    remaining_amount: Optional[float] = None
    average_price: Optional[float] = None
    fee_cost: float
    reason: Optional[str] = None
    trigger: Optional[str] = None


class OrderSummaryResponse(BaseModel):
    total_orders: int
    active_orders: int
    filled_orders: int
    cancelled_orders: int
    expired_orders: int
    rejected_orders: int
    total_volume: float
    total_fees: float
    avg_fill_time: float
    fill_rate: float
    last_update: Optional[datetime]
    exchanges: List[str]
    symbols: List[str]


class OrderPerformanceResponse(BaseModel):
    execution_speed: float
    order_reliability: float
    cost_efficiency: float
    avg_order_size: float


class OrderMetricsResponse(BaseModel):
    date: datetime
    exchange: str
    symbol: Optional[str] = None
    total_orders: int
    successful_orders: int
    failed_orders: int
    filled_orders: int
    cancelled_orders: int
    expired_orders: int
    market_orders: int
    limit_orders: int
    stop_orders: int
    buy_orders: int
    sell_orders: int
    fill_rate: float
    avg_fill_time: float
    total_volume: float
    total_fees: float
    order_accuracy: float
    error_rate: float


# Create router
order_router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# Initialize dependencies
order_manager = None


def get_order_manager():
    """Get order manager instance."""
    global order_manager
    if order_manager is None:
        order_manager = OrderManager()
    return order_manager


@order_router.get("/", response_model=List[OrderResponse])
async def get_all_orders(
    status: Optional[str] = Query(None, description="Filter by status (open, filled, cancelled, etc.)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    order_type: Optional[str] = Query(None, description="Filter by order type"),
    side: Optional[str] = Query(None, description="Filter by side (buy/sell)"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get all orders with optional filtering."""
    session = get_session()

    try:
        # Build query
        query = session.query(Order)

        # Apply filters
        if status:
            query = query.filter(Order.status.ilike(f"%{status}%"))
        if exchange:
            query = query.filter(Order.exchange == exchange)
        if symbol:
            query = query.filter(Order.symbol == symbol)
        if order_type:
            query = query.filter(Order.order_type.ilike(f"%{order_type}%"))
        if side:
            query = query.filter(Order.side.ilike(f"%{side}%"))
        if start_time:
            query = query.filter(Order.created_at >= start_time)
        if end_time:
            query = query.filter(Order.created_at <= end_time)

        # Apply limit and order
        query = query.order_by(Order.updated_at.desc()).limit(limit)

        # Execute query
        orders = query.all()
        session.close()

        # Convert to response format
        return [
            OrderResponse(
                id=str(order.id),
                exchange=order.exchange,
                symbol=order.symbol,
                order_id=order.order_id,
                client_order_id=order.client_order_id,
                order_type=order.order_type.value,
                side=order.side.value,
                status=order.status.value,
                price=order.price,
                amount=order.amount,
                filled_amount=order.filled_amount,
                remaining_amount=order.remaining_amount,
                cost=order.cost,
                average_price=order.average_price,
                fee_cost=order.fee_cost,
                fee_currency=order.fee_currency,
                created_at=order.created_at,
                updated_at=order.updated_at,
                filled_at=order.fill_timestamp,
                cancelled_at=order.cancel_timestamp,
                fill_rate=order.get_fill_rate(),
                is_active=order.is_active(),
                is_expired=order.is_expired()
            )
            for order in orders
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")


@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get a specific order by ID."""
    session = get_session()

    try:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        session.close()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderResponse(
            id=str(order.id),
            exchange=order.exchange,
            symbol=order.symbol,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            order_type=order.order_type.value,
            side=order.side.value,
            status=order.status.value,
            price=order.price,
            amount=order.amount,
            filled_amount=order.filled_amount,
            remaining_amount=order.remaining_amount,
            cost=order.cost,
            average_price=order.average_price,
            fee_cost=order.fee_cost,
            fee_currency=order.fee_currency,
            created_at=order.created_at,
            updated_at=order.updated_at,
            filled_at=order.fill_timestamp,
            cancelled_at=order.cancel_timestamp,
            fill_rate=order.get_fill_rate(),
            is_active=order.is_active(),
            is_expired=order.is_expired()
        )

    except HTTPException:
        raise
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")


@order_router.get("/exchange/{exchange}", response_model=List[OrderResponse])
async def get_orders_by_exchange(
    exchange: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get orders for a specific exchange."""
    manager = get_order_manager()
    try:
        orders = await manager.get_orders_by_exchange(exchange, symbol)

        # Apply status filter
        if status:
            orders = [o for o in orders if status.lower() in o.get('status', '').lower()]

        # Apply limit
        orders = orders[:limit]

        return [OrderResponse(**order) for order in orders]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orders for {exchange}: {str(e)}")


@order_router.get("/symbol/{symbol}", response_model=List[OrderResponse])
async def get_orders_by_symbol(
    symbol: str,
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get orders for a specific symbol."""
    manager = get_order_manager()
    try:
        orders = await manager.get_orders_by_symbol(symbol, exchange)

        # Apply status filter
        if status:
            orders = [o for o in orders if status.lower() in o.get('status', '').lower()]

        # Apply limit
        orders = orders[:limit]

        return [OrderResponse(**order) for order in orders]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orders for {symbol}: {str(e)}")


@order_router.get("/history/{order_id}", response_model=List[OrderHistoryResponse])
async def get_order_history(
    order_id: str,
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get history for a specific order."""
    session = get_session()

    try:
        # Find the order first
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Get history records
        history_records = session.query(OrderHistory).filter(
            OrderHistory.order_id == order.id
        ).order_by(OrderHistory.event_timestamp.desc()).limit(limit).all()

        session.close()

        return [
            OrderHistoryResponse(
                id=str(record.id),
                order_id=str(record.order_id),
                event_type=record.event_type,
                event_timestamp=record.event_timestamp,
                status=record.status.value if record.status else None,
                filled_amount=record.filled_amount,
                remaining_amount=record.remaining_amount,
                average_price=record.average_price,
                fee_cost=record.fee_cost,
                reason=record.reason,
                trigger=record.trigger
            )
            for record in history_records
        ]

    except HTTPException:
        raise
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get order history: {str(e)}")


@order_router.get("/summary", response_model=OrderSummaryResponse)
async def get_order_summary():
    """Get order summary statistics."""
    manager = get_order_manager()
    try:
        summary = await manager.get_order_summary()
        return OrderSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order summary: {str(e)}")


@order_router.get("/performance", response_model=OrderPerformanceResponse)
async def get_order_performance():
    """Get order performance metrics."""
    manager = get_order_manager()
    try:
        performance = await manager.get_order_performance_metrics()
        return OrderPerformanceResponse(**performance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order performance: {str(e)}")


@order_router.get("/metrics", response_model=List[OrderMetricsResponse])
async def get_order_metrics(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(30, description="Maximum number of records", ge=1, le=365)
):
    """Get order metrics."""
    session = get_session()

    try:
        # Build query
        query = session.query(OrderMetrics)

        # Apply filters
        if exchange:
            query = query.filter(OrderMetrics.exchange == exchange)
        if symbol:
            query = query.filter(OrderMetrics.symbol == symbol)
        if start_date:
            query = query.filter(OrderMetrics.date >= start_date)
        if end_date:
            query = query.filter(OrderMetrics.date <= end_date)

        # Apply limit and order
        query = query.order_by(OrderMetrics.date.desc()).limit(limit)

        # Execute query
        metrics_records = query.all()
        session.close()

        return [
            OrderMetricsResponse(
                date=record.date,
                exchange=record.exchange,
                symbol=record.symbol,
                total_orders=record.total_orders,
                successful_orders=record.successful_orders,
                failed_orders=record.failed_orders,
                filled_orders=record.filled_orders,
                cancelled_orders=record.cancelled_orders,
                expired_orders=record.expired_orders,
                market_orders=record.market_orders,
                limit_orders=record.limit_orders,
                stop_orders=record.stop_orders,
                buy_orders=record.buy_orders,
                sell_orders=record.sell_orders,
                fill_rate=record.fill_rate,
                avg_fill_time=record.avg_fill_time,
                total_volume=record.total_volume,
                total_fees=record.total_fees,
                order_accuracy=record.order_accuracy,
                error_rate=record.error_rate
            )
            for record in metrics_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get order metrics: {str(e)}")


@order_router.get("/analysis")
async def get_order_analysis(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    days: int = Query(7, description="Number of days to analyze", ge=1, le=365)
):
    """Get comprehensive order analysis."""
    session = get_session()

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Build query
        query = session.query(Order).filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )

        # Apply filters
        if exchange:
            query = query.filter(Order.exchange == exchange)
        if symbol:
            query = query.filter(Order.symbol == symbol)

        # Execute query
        orders = query.all()
        session.close()

        if not orders:
            return {
                "total_orders": 0,
                "execution_analysis": {},
                "cost_analysis": {},
                "timing_analysis": {},
                "type_analysis": {},
                "recommendations": []
            }

        # Execution analysis
        filled_orders = [o for o in orders if o.status == OrderStatus.FILLED]
        cancelled_orders = [o for o in orders if o.status == OrderStatus.CANCELED]
        expired_orders = [o for o in orders if o.status == OrderStatus.EXPIRED]

        execution_analysis = {
            "total_orders": len(orders),
            "filled_orders": len(filled_orders),
            "cancelled_orders": len(cancelled_orders),
            "expired_orders": len(expired_orders),
            "fill_rate": len(filled_orders) / len(orders) if orders else 0,
            "cancellation_rate": len(cancelled_orders) / len(orders) if orders else 0,
            "expiration_rate": len(expired_orders) / len(orders) if orders else 0
        }

        # Cost analysis
        total_volume = sum(o.filled_amount for o in filled_orders)
        total_fees = sum(o.fee_cost for o in orders)
        avg_fee_rate = (total_fees / total_volume * 100) if total_volume > 0 else 0

        cost_analysis = {
            "total_volume": total_volume,
            "total_fees": total_fees,
            "avg_fee_rate": avg_fee_rate,
            "fees_by_currency": {}
        }

        # Group fees by currency
        fee_currencies = {}
        for order in orders:
            if order.fee_currency and order.fee_cost > 0:
                if order.fee_currency not in fee_currencies:
                    fee_currencies[order.fee_currency] = 0
                fee_currencies[order.fee_currency] += order.fee_cost

        cost_analysis["fees_by_currency"] = fee_currencies

        # Timing analysis
        fill_times = []
        for order in filled_orders:
            if order.fill_timestamp and order.created_at:
                fill_time = (order.fill_timestamp - order.created_at).total_seconds()
                fill_times.append(fill_time)

        timing_analysis = {
            "avg_fill_time": sum(fill_times) / len(fill_times) if fill_times else 0,
            "min_fill_time": min(fill_times) if fill_times else 0,
            "max_fill_time": max(fill_times) if fill_times else 0,
            "fast_fills": len([t for t in fill_times if t < 1.0]),  # Less than 1 second
            "slow_fills": len([t for t in fill_times if t > 30.0])  # More than 30 seconds
        }

        # Type analysis
        type_counts = {}
        side_counts = {}

        for order in orders:
            order_type = order.order_type.value
            side = order.side.value

            type_counts[order_type] = type_counts.get(order_type, 0) + 1
            side_counts[side] = side_counts.get(side, 0) + 1

        type_analysis = {
            "order_types": type_counts,
            "sides": side_counts
        }

        # Generate recommendations
        recommendations = []

        if execution_analysis["fill_rate"] < 0.8:
            recommendations.append("Low fill rate detected. Consider adjusting order placement strategy.")

        if timing_analysis["avg_fill_time"] > 10:
            recommendations.append("Slow order execution detected. Check exchange connectivity and latency.")

        if cost_analysis["avg_fee_rate"] > 0.2:
            recommendations.append("High fee rates detected. Consider using limit orders or fee optimization.")

        if len(recommendations) == 0:
            recommendations.append("Order performance looks good. Continue current strategy.")

        return {
            "total_orders": len(orders),
            "execution_analysis": execution_analysis,
            "cost_analysis": cost_analysis,
            "timing_analysis": timing_analysis,
            "type_analysis": type_analysis,
            "recommendations": recommendations
        }

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get order analysis: {str(e)}")


@order_router.post("/sync")
async def sync_orders():
    """Manually trigger order synchronization."""
    manager = get_order_manager()
    try:
        await manager.sync_all_orders()
        return {"status": "success", "message": "Orders synchronized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync orders: {str(e)}")


@order_router.get("/updates")
async def get_order_updates(
    timeout: float = Query(1.0, description="Timeout in seconds", ge=0.1, le=30.0),
    limit: int = Query(100, description="Maximum number of updates", ge=1, le=1000)
):
    """Get real-time order updates."""
    manager = get_order_manager()
    try:
        updates = await manager.get_order_updates(timeout=timeout)
        return [
            {
                "order_id": update.order_id,
                "exchange": update.exchange,
                "symbol": update.symbol,
                "update_type": update.update_type,
                "timestamp": update.timestamp.isoformat(),
                "old_order": update.old_order,
                "new_order": update.new_order
            }
            for update in updates[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order updates: {str(e)}")


@order_router.get("/types", response_model=List[str])
async def get_order_types():
    """Get available order types."""
    return [order_type.value for order_type in OrderType]


@order_router.get("/sides", response_model=List[str])
async def get_order_sides():
    """Get available order sides."""
    return [side.value for side in OrderSide]


@order_router.get("/statuses", response_model=List[str])
async def get_order_statuses():
    """Get available order statuses."""
    return [status.value for status in OrderStatus]
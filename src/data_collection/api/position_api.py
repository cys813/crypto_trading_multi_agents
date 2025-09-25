"""
Position data API endpoints for the data collection agent.

This module provides RESTful API endpoints for accessing position data,
including current positions, position history, and position statistics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ..core.position_manager import PositionManager
from ..models.position import Position, PositionHistory, PositionMetrics
from ..models.database import get_session
from ..utils.helpers import format_timestamp


# Pydantic models for API requests/responses
class PositionResponse(BaseModel):
    id: str
    exchange: str
    symbol: str
    position_id: str
    position_type: str
    status: str
    size: float
    entry_price: float
    mark_price: Optional[float] = None
    leverage: float
    margin: Optional[float] = None
    pnl: float
    unrealized_pnl: float
    realized_pnl: float
    roi: float
    opened_at: datetime
    closed_at: Optional[datetime] = None
    duration: Optional[str] = None
    total_fees: float
    risk_metrics: Optional[Dict[str, Any]] = None


class PositionHistoryResponse(BaseModel):
    id: str
    position_id: str
    event_type: str
    event_timestamp: datetime
    size: float
    entry_price: float
    mark_price: Optional[float] = None
    pnl: float
    unrealized_pnl: float
    realized_pnl: float
    reason: Optional[str] = None
    trigger: Optional[str] = None
    fees_incurred: float


class PositionSummaryResponse(BaseModel):
    total_positions: int
    active_positions: int
    closed_positions: int
    liquidated_positions: int
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    last_update: Optional[datetime]
    exchanges: List[str]
    symbols: List[str]


class PositionRiskResponse(BaseModel):
    total_exposure: float
    max_exposure: float
    leverage_usage: float
    risk_positions: int
    liquidation_risk: float
    positions_at_risk: List[Dict[str, Any]]


class PositionMetricsResponse(BaseModel):
    date: datetime
    exchange: str
    symbol: Optional[str] = None
    total_positions: int
    open_positions: int
    closed_positions: int
    liquidated_positions: int
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    total_fees: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float


# Create router
position_router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

# Initialize dependencies
position_manager = None


def get_position_manager():
    """Get position manager instance."""
    global position_manager
    if position_manager is None:
        position_manager = PositionManager()
    return position_manager


@position_router.get("/", response_model=List[PositionResponse])
async def get_all_positions(
    status: Optional[str] = Query(None, description="Filter by status (open, closed, liquidated)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get all positions with optional filtering."""
    session = get_session()

    try:
        # Build query
        query = session.query(Position)

        # Apply filters
        if status:
            query = query.filter(Position.status.ilike(f"%{status}%"))
        if exchange:
            query = query.filter(Position.exchange == exchange)
        if symbol:
            query = query.filter(Position.symbol == symbol)

        # Apply limit and order
        query = query.order_by(Position.updated_at.desc()).limit(limit)

        # Execute query
        positions = query.all()
        session.close()

        # Convert to response format
        return [
            PositionResponse(
                id=str(position.id),
                exchange=position.exchange,
                symbol=position.symbol,
                position_id=position.position_id,
                position_type=position.position_type.value,
                status=position.status.value,
                size=position.size,
                entry_price=position.entry_price,
                mark_price=position.mark_price,
                leverage=position.leverage,
                margin=position.margin,
                pnl=position.pnl,
                unrealized_pnl=position.unrealized_pnl,
                realized_pnl=position.realized_pnl,
                roi=position.roi,
                opened_at=position.opened_at,
                closed_at=position.closed_at,
                duration=position.duration,
                total_fees=position.total_fees,
                risk_metrics=position.get_risk_metrics()
            )
            for position in positions
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@position_router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str):
    """Get a specific position by ID."""
    session = get_session()

    try:
        position = session.query(Position).filter(Position.id == position_id).first()
        session.close()

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        return PositionResponse(
            id=str(position.id),
            exchange=position.exchange,
            symbol=position.symbol,
            position_id=position.position_id,
            position_type=position.position_type.value,
            status=position.status.value,
            size=position.size,
            entry_price=position.entry_price,
            mark_price=position.mark_price,
            leverage=position.leverage,
            margin=position.margin,
            pnl=position.pnl,
            unrealized_pnl=position.unrealized_pnl,
            realized_pnl=position.realized_pnl,
            roi=position.roi,
            opened_at=position.opened_at,
            closed_at=position.closed_at,
            duration=position.duration,
            total_fees=position.total_fees,
            risk_metrics=position.get_risk_metrics()
        )

    except HTTPException:
        raise
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")


@position_router.get("/exchange/{exchange}", response_model=List[PositionResponse])
async def get_positions_by_exchange(
    exchange: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get positions for a specific exchange."""
    manager = get_position_manager()
    try:
        positions = await manager.get_positions_by_exchange(exchange)

        # Apply status filter
        if status:
            positions = [p for p in positions if status.lower() in p.get('status', '').lower()]

        # Apply limit
        positions = positions[:limit]

        return [PositionResponse(**position) for position in positions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions for {exchange}: {str(e)}")


@position_router.get("/symbol/{symbol}", response_model=List[PositionResponse])
async def get_positions_by_symbol(
    symbol: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get positions for a specific symbol."""
    manager = get_position_manager()
    try:
        positions = await manager.get_positions_by_symbol(symbol)

        # Apply status filter
        if status:
            positions = [p for p in positions if status.lower() in p.get('status', '').lower()]

        # Apply limit
        positions = positions[:limit]

        return [PositionResponse(**position) for position in positions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions for {symbol}: {str(e)}")


@position_router.get("/history/{position_id}", response_model=List[PositionHistoryResponse])
async def get_position_history(
    position_id: str,
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000)
):
    """Get history for a specific position."""
    session = get_session()

    try:
        history_records = session.query(PositionHistory).filter(
            PositionHistory.position_id == position_id
        ).order_by(PositionHistory.event_timestamp.desc()).limit(limit).all()

        session.close()

        return [
            PositionHistoryResponse(
                id=str(record.id),
                position_id=str(record.position_id),
                event_type=record.event_type,
                event_timestamp=record.event_timestamp,
                size=record.size,
                entry_price=record.entry_price,
                mark_price=record.mark_price,
                pnl=record.pnl,
                unrealized_pnl=record.unrealized_pnl,
                realized_pnl=record.realized_pnl,
                reason=record.reason,
                trigger=record.trigger,
                fees_incurred=record.fees_incurred
            )
            for record in history_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get position history: {str(e)}")


@position_router.get("/summary", response_model=PositionSummaryResponse)
async def get_position_summary():
    """Get position summary statistics."""
    manager = get_position_manager()
    try:
        summary = await manager.get_position_summary()
        return PositionSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position summary: {str(e)}")


@position_router.get("/risk", response_model=PositionRiskResponse)
async def get_position_risk():
    """Get position risk metrics."""
    manager = get_position_manager()
    try:
        risk_metrics = await manager.get_position_risk_metrics()

        # Get positions at risk
        session = get_session()
        try:
            positions_at_risk = []
            active_positions = session.query(Position).filter(
                Position.status.in_(['open', 'partially_closed'])
            ).all()

            for position in active_positions:
                risk_data = position.get_risk_metrics()
                distance_to_liq = risk_data.get('distance_to_liquidation_percent', 100)

                if distance_to_liq < 10:  # Less than 10% from liquidation
                    positions_at_risk.append({
                        'position_id': str(position.id),
                        'symbol': position.symbol,
                        'exchange': position.exchange,
                        'distance_to_liquidation': distance_to_liq,
                        'pnl': position.pnl,
                        'leverage': position.leverage
                    })

            risk_metrics['positions_at_risk'] = positions_at_risk[:10]  # Limit to 10 positions

        finally:
            session.close()

        return PositionRiskResponse(**risk_metrics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position risk: {str(e)}")


@position_router.get("/metrics", response_model=List[PositionMetricsResponse])
async def get_position_metrics(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(30, description="Maximum number of records", ge=1, le=365)
):
    """Get position performance metrics."""
    session = get_session()

    try:
        # Build query
        query = session.query(PositionMetrics)

        # Apply filters
        if exchange:
            query = query.filter(PositionMetrics.exchange == exchange)
        if symbol:
            query = query.filter(PositionMetrics.symbol == symbol)
        if start_date:
            query = query.filter(PositionMetrics.date >= start_date)
        if end_date:
            query = query.filter(PositionMetrics.date <= end_date)

        # Apply limit and order
        query = query.order_by(PositionMetrics.date.desc()).limit(limit)

        # Execute query
        metrics_records = query.all()
        session.close()

        return [
            PositionMetricsResponse(
                date=record.date,
                exchange=record.exchange,
                symbol=record.symbol,
                total_positions=record.total_positions,
                open_positions=record.open_positions,
                closed_positions=record.closed_positions,
                liquidated_positions=record.liquidated_positions,
                total_pnl=record.total_pnl,
                realized_pnl=record.realized_pnl,
                unrealized_pnl=record.unrealized_pnl,
                total_fees=record.total_fees,
                win_rate=record.win_rate,
                avg_win=record.avg_win,
                avg_loss=record.avg_loss,
                profit_factor=record.profit_factor,
                max_drawdown=record.max_drawdown
            )
            for record in metrics_records
        ]

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get position metrics: {str(e)}")


@position_router.get("/performance")
async def get_position_performance(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Get position performance analysis."""
    session = get_session()

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Build query
        query = session.query(Position).filter(
            Position.opened_at >= start_date,
            Position.opened_at <= end_date
        )

        # Apply filters
        if exchange:
            query = query.filter(Position.exchange == exchange)
        if symbol:
            query = query.filter(Position.symbol == symbol)

        # Execute query
        positions = query.all()
        session.close()

        if not positions:
            return {
                "total_positions": 0,
                "winning_positions": 0,
                "losing_positions": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0
            }

        # Calculate performance metrics
        closed_positions = [p for p in positions if p.status.value in ['closed', 'liquidated']]
        winning_positions = [p for p in closed_positions if p.pnl > 0]
        losing_positions = [p for p in closed_positions if p.pnl < 0]

        total_pnl = sum(p.pnl for p in closed_positions)
        total_win = sum(p.pnl for p in winning_positions)
        total_loss = abs(sum(p.pnl for p in losing_positions))

        win_rate = len(winning_positions) / len(closed_positions) if closed_positions else 0
        avg_win = total_win / len(winning_positions) if winning_positions else 0
        avg_loss = total_loss / len(losing_positions) if losing_positions else 0
        profit_factor = total_win / total_loss if total_loss > 0 else 0

        # Calculate max drawdown (simplified)
        pnl_history = []
        running_pnl = 0
        for position in sorted(positions, key=lambda x: x.opened_at):
            if position.status.value in ['closed', 'liquidated']:
                running_pnl += position.pnl
                pnl_history.append(running_pnl)

        max_drawdown = 0
        if pnl_history:
            peak = pnl_history[0]
            for pnl in pnl_history:
                if pnl > peak:
                    peak = pnl
                drawdown = (peak - pnl) / peak if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)

        return {
            "total_positions": len(positions),
            "winning_positions": len(winning_positions),
            "losing_positions": len(losing_positions),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown * 100  # Convert to percentage
        }

    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=f"Failed to get position performance: {str(e)}")


@position_router.post("/sync")
async def sync_positions():
    """Manually trigger position synchronization."""
    manager = get_position_manager()
    try:
        await manager.sync_all_positions()
        return {"status": "success", "message": "Positions synchronized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync positions: {str(e)}")


@position_router.get("/updates")
async def get_position_updates(
    timeout: float = Query(1.0, description="Timeout in seconds", ge=0.1, le=30.0),
    limit: int = Query(100, description="Maximum number of updates", ge=1, le=1000)
):
    """Get real-time position updates."""
    manager = get_position_manager()
    try:
        updates = await manager.get_position_updates(timeout=timeout)
        return [
            {
                "position_id": update.position_id,
                "exchange": update.exchange,
                "symbol": update.symbol,
                "update_type": update.update_type,
                "timestamp": update.timestamp.isoformat(),
                "old_position": update.old_position,
                "new_position": update.new_position
            }
            for update in updates[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position updates: {str(e)}")
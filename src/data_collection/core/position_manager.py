"""
Position Manager for managing trading position information.

This module provides functionality for collecting, tracking, and analyzing
position data from multiple cryptocurrency exchanges, including real-time
position monitoring, PnL calculation, and risk management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import uuid

from .exchange_manager import ExchangeManager
from ..config.settings import get_settings
from ..models.database import get_session
from ..models.position import Position, PositionHistory, PositionMetrics, PositionType, PositionStatus
from ..utils.metrics import MetricsCollector
from ..utils.helpers import calculate_pnl, safe_float_conversion


@dataclass
class PositionUpdate:
    """Represents a position update."""
    position_id: str
    exchange: str
    symbol: str
    update_type: str  # 'create', 'update', 'close', 'liquidate'
    old_position: Optional[Dict] = None
    new_position: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class PositionManager:
    """Manages position data from multiple exchanges."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.exchange_manager = ExchangeManager()
        self.metrics = MetricsCollector()

        # Position tracking
        self.positions: Dict[str, Position] = {}  # position_id -> Position
        self.positions_by_exchange: Dict[str, Dict[str, Position]] = {}  # exchange -> symbol -> Position
        self.positions_by_symbol: Dict[str, Dict[str, Position]] = {}  # symbol -> exchange -> Position

        # Position updates queue
        self.update_queue = asyncio.Queue()
        self.position_callbacks = []

        # Monitoring and statistics
        self.stats = {
            'total_positions': 0,
            'active_positions': 0,
            'closed_positions': 0,
            'liquidated_positions': 0,
            'total_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'last_update': None,
            'monitored_exchanges': 0,
            'monitored_symbols': 0
        }

        # Background tasks
        self.monitor_task = None
        self.sync_task = None
        self.history_task = None

        # Monitoring settings
        self.sync_interval = 30  # seconds
        self.history_interval = 300  # 5 minutes

    async def start(self):
        """Start the position manager."""
        self.logger.info("Starting position manager")

        # Start background tasks
        await self.start_monitoring()
        await self.start_sync()
        await self.start_history_tracking()

        # Initial sync
        await self.sync_all_positions()

        self.logger.info("Position manager started")

    async def stop(self):
        """Stop the position manager."""
        self.logger.info("Stopping position manager")

        # Cancel background tasks
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        if self.history_task:
            self.history_task.cancel()
            try:
                await self.history_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Position manager stopped")

    async def start_monitoring(self):
        """Start position monitoring task."""
        async def monitor():
            while True:
                try:
                    await self.update_positions()
                    await asyncio.sleep(self.sync_interval)
                except Exception as e:
                    self.logger.error(f"Position monitoring error: {e}")
                    await asyncio.sleep(10)  # Wait before retrying

        self.monitor_task = asyncio.create_task(monitor())

    async def start_sync(self):
        """Start position sync task."""
        async def sync():
            while True:
                try:
                    await self.sync_all_positions()
                    await asyncio.sleep(self.sync_interval)
                except Exception as e:
                    self.logger.error(f"Position sync error: {e}")
                    await asyncio.sleep(10)  # Wait before retrying

        self.sync_task = asyncio.create_task(sync())

    async def start_history_tracking(self):
        """Start position history tracking task."""
        async def track_history():
            while True:
                try:
                    await self.record_position_history()
                    await asyncio.sleep(self.history_interval)
                except Exception as e:
                    self.logger.error(f"Position history tracking error: {e}")
                    await asyncio.sleep(30)  # Wait before retrying

        self.history_task = asyncio.create_task(track_history())

    async def sync_all_positions(self):
        """Sync positions from all exchanges."""
        exchanges = await self.exchange_manager.get_all_exchanges()

        for exchange in exchanges:
            try:
                await self.sync_exchange_positions(exchange)
            except Exception as e:
                self.logger.error(f"Failed to sync positions for {exchange}: {e}")

    async def sync_exchange_positions(self, exchange: str):
        """Sync positions from a specific exchange."""
        try:
            # Get positions from exchange
            raw_positions = await self.exchange_manager.get_positions(exchange)

            if not raw_positions:
                return

            # Process each position
            for raw_position in raw_positions:
                await self.process_position_update(exchange, raw_position)

            # Update statistics
            self.stats['monitored_exchanges'] = len(self.positions_by_exchange)
            self.stats['monitored_symbols'] = sum(len(positions) for positions in self.positions_by_exchange.values())

        except Exception as e:
            self.logger.error(f"Failed to sync positions from {exchange}: {e}")

    async def process_position_update(self, exchange: str, raw_position: Dict):
        """Process a single position update."""
        try:
            # Extract position details
            symbol = raw_position.get('symbol')
            position_id = raw_position.get('id') or f"{exchange}_{symbol}_{uuid.uuid4().hex[:8]}"

            if not symbol:
                self.logger.warning(f"Position update missing symbol: {raw_position}")
                return

            # Create or update position
            position = await self._create_or_update_position(exchange, symbol, position_id, raw_position)

            if position:
                # Update tracking
                await self._update_position_tracking(position)

                # Queue update
                update = PositionUpdate(
                    position_id=position_id,
                    exchange=exchange,
                    symbol=symbol,
                    update_type='update',
                    new_position=position.to_dict()
                )
                await self.update_queue.put(update)

                # Notify callbacks
                await self._notify_position_callbacks(update)

        except Exception as e:
            self.logger.error(f"Failed to process position update: {e}")

    async def _create_or_update_position(self, exchange: str, symbol: str, position_id: str,
                                       raw_position: Dict) -> Optional[Position]:
        """Create or update a position in the database."""
        try:
            session = get_session()

            # Check if position exists
            existing_position = session.query(Position).filter(
                Position.position_id == position_id
            ).first()

            # Extract position data
            position_type = self._determine_position_type(raw_position)
            size = safe_float_conversion(raw_position.get('size', raw_position.get('contracts')))
            entry_price = safe_float_conversion(raw_position.get('entryPrice', raw_position.get('average_price')))
            mark_price = safe_float_conversion(raw_position.get('markPrice', raw_position.get('last_price')))
            leverage = safe_float_conversion(raw_position.get('leverage', 1.0))
            margin = safe_float_conversion(raw_position.get('margin', raw_position.get('initialMargin')))
            unrealized_pnl = safe_float_conversion(raw_position.get('unrealizedPnl', raw_position.get('pnl')))
            realized_pnl = safe_float_conversion(raw_position.get('realizedPnl', 0.0))
            liquidation_price = safe_float_conversion(raw_position.get('liquidationPrice'))

            # Determine position status
            status = self._determine_position_status(raw_position, size)

            if existing_position:
                # Update existing position
                update_data = {
                    'size': size,
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'leverage': leverage,
                    'margin': margin,
                    'unrealized_pnl': unrealized_pnl,
                    'realized_pnl': realized_pnl,
                    'pnl': unrealized_pnl + realized_pnl,
                    'liquidation_price': liquidation_price,
                    'status': status,
                    'last_sync': datetime.now(timezone.utc)
                }

                # Update fields
                for key, value in update_data.items():
                    if value is not None:
                        setattr(existing_position, key, value)

                # Update duration
                existing_position.calculate_duration()

                session.commit()
                position = existing_position

            else:
                # Create new position
                position = Position(
                    exchange=exchange,
                    symbol=symbol,
                    position_id=position_id,
                    position_type=position_type,
                    size=size,
                    entry_price=entry_price,
                    mark_price=mark_price,
                    leverage=leverage,
                    margin=margin,
                    unrealized_pnl=unrealized_pnl,
                    realized_pnl=realized_pnl,
                    pnl=unrealized_pnl + realized_pnl,
                    liquidation_price=liquidation_price,
                    status=status,
                    opened_at=datetime.now(timezone.utc),
                    last_sync=datetime.now(timezone.utc)
                )

                session.add(position)
                session.commit()

            session.close()
            return position

        except Exception as e:
            self.logger.error(f"Failed to create/update position {position_id}: {e}")
            return None

    def _determine_position_type(self, raw_position: Dict) -> PositionType:
        """Determine position type from raw data."""
        side = raw_position.get('side', '').lower()
        size = safe_float_conversion(raw_position.get('size', 0))

        if size > 0:
            if side == 'long' or side == 'buy':
                return PositionType.LONG
            elif side == 'short' or side == 'sell':
                return PositionType.SHORT

        return PositionType.LONG  # Default

    def _determine_position_status(self, raw_position: Dict, size: float) -> PositionStatus:
        """Determine position status from raw data."""
        if abs(size) < 1e-8:  # Very small size
            return PositionStatus.CLOSED

        status = raw_position.get('status', '').lower()

        if 'liquidat' in status:
            return PositionStatus.LIQUIDATED
        elif 'close' in status:
            return PositionStatus.CLOSED
        elif size > 0:
            return PositionStatus.OPEN
        else:
            return PositionStatus.CLOSED

    async def _update_position_tracking(self, position: Position):
        """Update internal position tracking."""
        position_id = str(position.id)
        exchange = position.exchange
        symbol = position.symbol

        # Update main tracking
        self.positions[position_id] = position

        # Update by exchange
        if exchange not in self.positions_by_exchange:
            self.positions_by_exchange[exchange] = {}
        self.positions_by_exchange[exchange][symbol] = position

        # Update by symbol
        if symbol not in self.positions_by_symbol:
            self.positions_by_symbol[symbol] = {}
        self.positions_by_symbol[symbol][exchange] = position

        # Update statistics
        await self._update_position_stats()

    async def _update_position_stats(self):
        """Update position statistics."""
        active_positions = [p for p in self.positions.values() if p.status == PositionStatus.OPEN]

        self.stats['total_positions'] = len(self.positions)
        self.stats['active_positions'] = len(active_positions)
        self.stats['closed_positions'] = len([p for p in self.positions.values() if p.status == PositionStatus.CLOSED])
        self.stats['liquidated_positions'] = len([p for p in self.positions.values() if p.status == PositionStatus.LIQUIDATED])

        if active_positions:
            self.stats['unrealized_pnl'] = sum(p.unrealized_pnl for p in active_positions)
            self.stats['realized_pnl'] = sum(p.realized_pnl for p in active_positions)
            self.stats['total_pnl'] = sum(p.pnl for p in active_positions)
        else:
            self.stats['unrealized_pnl'] = 0.0
            self.stats['realized_pnl'] = 0.0
            self.stats['total_pnl'] = 0.0

        self.stats['last_update'] = datetime.now(timezone.utc)

    async def update_positions(self):
        """Update all active positions with current prices."""
        try:
            # Get unique symbols across all exchanges
            symbols = set()
            for exchange_positions in self.positions_by_exchange.values():
                symbols.update(exchange_positions.keys())

            # Get current prices for all symbols
            for symbol in symbols:
                for exchange, positions in self.positions_by_exchange.items():
                    if symbol in positions:
                        position = positions[symbol]
                        if position.status == PositionStatus.OPEN:
                            await self._update_position_price(exchange, symbol, position)

        except Exception as e:
            self.logger.error(f"Failed to update positions: {e}")

    async def _update_position_price(self, exchange: str, symbol: str, position: Position):
        """Update a single position with current price."""
        try:
            # Get current ticker price
            ticker = await self.exchange_manager.get_ticker(exchange, symbol)
            if ticker and 'last' in ticker:
                current_price = safe_float_conversion(ticker['last'])
                if current_price > 0:
                    position.update_pnl(current_price)

                    # Update database
                    session = get_session()
                    try:
                        db_position = session.query(Position).filter(
                            Position.id == position.id
                        ).first()
                        if db_position:
                            db_position.mark_price = current_price
                            db_position.update_pnl(current_price)
                            session.commit()
                    except Exception as e:
                        session.rollback()
                        self.logger.error(f"Failed to update position price in DB: {e}")
                    finally:
                        session.close()

        except Exception as e:
            self.logger.error(f"Failed to update position price for {exchange}/{symbol}: {e}")

    async def record_position_history(self):
        """Record position history for all active positions."""
        try:
            session = get_session()

            for position in self.positions.values():
                if position.status == PositionStatus.OPEN:
                    # Create history record
                    history = PositionHistory(
                        position_id=position.id,
                        event_type='update',
                        event_timestamp=datetime.now(timezone.utc),
                        size=position.size,
                        entry_price=position.entry_price,
                        mark_price=position.mark_price,
                        pnl=position.pnl,
                        unrealized_pnl=position.unrealized_pnl,
                        realized_pnl=position.realized_pnl,
                        cumulative_pnl=position.cumulative_pnl,
                        reason='periodic_update'
                    )

                    session.add(history)

            session.commit()
            session.close()

        except Exception as e:
            self.logger.error(f"Failed to record position history: {e}")

    async def get_position(self, position_id: str) -> Optional[Dict]:
        """Get position by ID."""
        position = self.positions.get(position_id)
        return position.to_dict() if position else None

    async def get_positions_by_exchange(self, exchange: str) -> List[Dict]:
        """Get all positions for an exchange."""
        positions = self.positions_by_exchange.get(exchange, {})
        return [position.to_dict() for position in positions.values()]

    async def get_positions_by_symbol(self, symbol: str) -> List[Dict]:
        """Get all positions for a symbol."""
        positions = self.positions_by_symbol.get(symbol, {})
        return [position.to_dict() for position in positions.values()]

    async def get_all_positions(self) -> List[Dict]:
        """Get all positions."""
        return [position.to_dict() for position in self.positions.values()]

    async def get_position_summary(self) -> Dict:
        """Get position summary statistics."""
        return {
            'total_positions': self.stats['total_positions'],
            'active_positions': self.stats['active_positions'],
            'closed_positions': self.stats['closed_positions'],
            'liquidated_positions': self.stats['liquidated_positions'],
            'total_pnl': self.stats['total_pnl'],
            'unrealized_pnl': self.stats['unrealized_pnl'],
            'realized_pnl': self.stats['realized_pnl'],
            'last_update': self.stats['last_update'].isoformat() if self.stats['last_update'] else None,
            'exchanges': list(self.positions_by_exchange.keys()),
            'symbols': list(self.positions_by_symbol.keys())
        }

    async def get_position_risk_metrics(self) -> Dict:
        """Get position risk metrics."""
        active_positions = [p for p in self.positions.values() if p.status == PositionStatus.OPEN]

        if not active_positions:
            return {
                'total_exposure': 0.0,
                'max_exposure': 0.0,
                'leverage_usage': 0.0,
                'risk_positions': 0,
                'liquidation_risk': 0.0
            }

        total_exposure = sum(abs(p.size * p.mark_price or p.entry_price) for p in active_positions)
        max_exposure = max(abs(p.size * (p.mark_price or p.entry_price)) for p in active_positions)
        avg_leverage = sum(p.leverage for p in active_positions) / len(active_positions)

        # Count positions with high risk
        risk_positions = 0
        liquidation_risk = 0.0

        for position in active_positions:
            risk_metrics = position.get_risk_metrics()

            # Check for liquidation risk
            distance_to_liq = risk_metrics.get('distance_to_liquidation_percent', 100)
            if distance_to_liq < 10:  # Less than 10% from liquidation
                risk_positions += 1
                liquidation_risk += (10 - distance_to_liq) / 10

        return {
            'total_exposure': total_exposure,
            'max_exposure': max_exposure,
            'leverage_usage': avg_leverage,
            'risk_positions': risk_positions,
            'liquidation_risk': liquidation_risk / len(active_positions) if active_positions else 0.0
        }

    def add_position_callback(self, callback):
        """Add a callback for position updates."""
        self.position_callbacks.append(callback)

    def remove_position_callback(self, callback):
        """Remove a position callback."""
        if callback in self.position_callbacks:
            self.position_callbacks.remove(callback)

    async def _notify_position_callbacks(self, update: PositionUpdate):
        """Notify all callbacks of position update."""
        for callback in self.position_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                self.logger.error(f"Position callback error: {e}")

    async def get_position_updates(self, timeout: float = 1.0) -> List[PositionUpdate]:
        """Get position updates from the queue."""
        updates = []
        start_time = asyncio.get_event_loop().time()

        while len(updates) < 100 and (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                update = await asyncio.wait_for(self.update_queue.get(), timeout=0.1)
                updates.append(update)
            except asyncio.TimeoutError:
                break

        return updates
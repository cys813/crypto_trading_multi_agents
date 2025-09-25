"""
Position Manager - Manages position data across multiple exchanges.

This module handles position tracking, PnL calculation, risk assessment,
and position synchronization across exchanges.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from decimal import Decimal
import json

from .exchange_manager import ExchangeManager

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position."""
    exchange: str
    symbol: str
    side: str  # 'long' or 'short'
    size: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    margin: Decimal
    leverage: int
    timestamp: datetime
    position_id: Optional[str] = None


@dataclass
class PositionHistory:
    """Tracks position changes over time."""
    position_id: str
    timestamp: datetime
    event_type: str  # 'open', 'close', 'update'
    data: Dict[str, Any]


class PositionManager:
    """Manages position data across multiple exchanges."""

    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self.positions: Dict[str, Position] = {}
        self.position_history: List[PositionHistory] = []
        self.last_update: Dict[str, datetime] = {}
        self.is_running = False
        self.stats = {
            'total_positions': 0,
            'active_positions': 0,
            'total_updates': 0,
            'failed_updates': 0,
            'last_sync_time': None
        }

    async def start(self):
        """Start position management."""
        logger.info("Starting position manager...")
        self.is_running = True

        # Initial sync
        await self.sync_all_positions()

        # Start periodic updates
        asyncio.create_task(self._periodic_sync())

        logger.info("Position manager started")

    async def stop(self):
        """Stop position management."""
        logger.info("Stopping position manager...")
        self.is_running = False
        logger.info("Position manager stopped")

    async def sync_all_positions(self):
        """Synchronize positions from all exchanges."""
        logger.info("Synchronizing positions from all exchanges...")

        for exchange_name in self.exchange_manager.config.keys():
            try:
                await self.sync_exchange_positions(exchange_name)
            except Exception as e:
                logger.error(f"Failed to sync positions for {exchange_name}: {e}")

        self.stats['last_sync_time'] = datetime.now()
        logger.info(f"Position sync completed. Active positions: {len(self.positions)}")

    async def sync_exchange_positions(self, exchange_name: str):
        """Synchronize positions from a specific exchange."""
        try:
            exchange = await self.exchange_manager.get_exchange(exchange_name)

            # Fetch positions
            positions_data = await exchange.fetch_positions()

            updated_count = 0
            for pos_data in positions_data:
                position = self._parse_position_data(exchange_name, pos_data)

                if position:
                    position_key = f"{exchange_name}_{position.symbol}"
                    old_position = self.positions.get(position_key)

                    # Update or add position
                    self.positions[position_key] = position
                    self.last_update[position_key] = datetime.now()

                    # Record position change
                    if old_position and old_position.size != position.size:
                        self._record_position_change(
                            position.position_id or position_key,
                            'update',
                            {
                                'old_size': float(old_position.size),
                                'new_size': float(position.size),
                                'pnl_change': float(position.unrealized_pnl - (old_position.unrealized_pnl if old_position else Decimal('0')))
                            }
                        )

                    updated_count += 1

            self.stats['total_updates'] += updated_count

            # Remove closed positions
            current_symbols = {pos['symbol'] for pos in positions_data}
            positions_to_remove = [
                key for key, pos in self.positions.items()
                if pos.exchange == exchange_name and pos.symbol not in current_symbols and pos.size != Decimal('0')
            ]

            for key in positions_to_remove:
                closed_position = self.positions[key]
                self._record_position_change(
                    closed_position.position_id or key,
                    'close',
                    {
                        'final_pnl': float(closed_position.unrealized_pnl + closed_position.realized_pnl),
                        'position_size': float(closed_position.size)
                    }
                )
                del self.positions[key]

            logger.debug(f"Synced {updated_count} positions from {exchange_name}")

        except Exception as e:
            self.stats['failed_updates'] += 1
            logger.error(f"Error syncing positions for {exchange_name}: {e}")

    def _parse_position_data(self, exchange_name: str, pos_data: Dict[str, Any]) -> Optional[Position]:
        """Parse position data from exchange format."""
        try:
            # Extract common fields
            symbol = pos_data.get('symbol', '')
            size = Decimal(str(pos_data.get('size', 0) or pos_data.get('contracts', 0)))
            entry_price = Decimal(str(pos_data.get('entryPrice', 0)))
            current_price = Decimal(str(pos_data.get('markPrice', pos_data.get('lastPrice', entry_price))))

            # Skip zero-sized positions
            if size == Decimal('0'):
                return None

            # Determine position side
            side = 'long' if size > Decimal('0') else 'short'
            abs_size = abs(size)

            # Calculate PnL
            if side == 'long':
                unrealized_pnl = (current_price - entry_price) * abs_size
            else:
                unrealized_pnl = (entry_price - current_price) * abs_size

            # Create position object
            position = Position(
                exchange=exchange_name,
                symbol=symbol,
                side=side,
                size=abs_size,
                entry_price=entry_price,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=Decimal(str(pos_data.get('realizedPnl', 0))),
                margin=Decimal(str(pos_data.get('margin', 0))),
                leverage=int(pos_data.get('leverage', 1)),
                timestamp=datetime.now(),
                position_id=pos_data.get('id')
            )

            return position

        except Exception as e:
            logger.error(f"Error parsing position data: {e}")
            return None

    async def _periodic_sync(self):
        """Periodically sync positions."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Sync every 30 seconds
                await self.sync_all_positions()
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")

    def _record_position_change(self, position_id: str, event_type: str, data: Dict[str, Any]):
        """Record a position change event."""
        history = PositionHistory(
            position_id=position_id,
            timestamp=datetime.now(),
            event_type=event_type,
            data=data
        )
        self.position_history.append(history)

        # Keep only last 1000 history entries
        if len(self.position_history) > 1000:
            self.position_history = self.position_history[-1000:]

    def get_position(self, exchange_name: str, symbol: str) -> Optional[Position]:
        """Get a specific position."""
        key = f"{exchange_name}_{symbol}"
        return self.positions.get(key)

    def get_all_positions(self) -> List[Position]:
        """Get all active positions."""
        return list(self.positions.values())

    def get_positions_by_exchange(self, exchange_name: str) -> List[Position]:
        """Get positions for a specific exchange."""
        return [pos for pos in self.positions.values() if pos.exchange == exchange_name]

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get positions for a specific symbol."""
        return [pos for pos in self.positions.values() if pos.symbol == symbol]

    def get_total_pnl(self) -> Tuple[Decimal, Decimal]:
        """Get total unrealized and realized PnL."""
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized = sum(pos.realized_pnl for pos in self.positions.values())
        return total_unrealized, total_realized

    def get_position_summary(self) -> Dict[str, Any]:
        """Get a summary of all positions."""
        positions = self.get_all_positions()
        total_unrealized, total_realized = self.get_total_pnl()

        summary = {
            'total_positions': len(positions),
            'active_positions': len([p for p in positions if p.size > 0]),
            'total_unrealized_pnl': float(total_unrealized),
            'total_realized_pnl': float(total_realized),
            'total_margin': sum(float(pos.margin) for pos in positions),
            'exchanges': {},
            'symbols': {},
            'risk_metrics': self._calculate_risk_metrics(positions)
        }

        # Group by exchange
        for pos in positions:
            if pos.exchange not in summary['exchanges']:
                summary['exchanges'][pos.exchange] = {
                    'positions': 0,
                    'unrealized_pnl': 0,
                    'realized_pnl': 0
                }

            summary['exchanges'][pos.exchange]['positions'] += 1
            summary['exchanges'][pos.exchange]['unrealized_pnl'] += float(pos.unrealized_pnl)
            summary['exchanges'][pos.exchange]['realized_pnl'] += float(pos.realized_pnl)

        # Group by symbol
        for pos in positions:
            if pos.symbol not in summary['symbols']:
                summary['symbols'][pos.symbol] = {
                    'positions': 0,
                    'unrealized_pnl': 0,
                    'realized_pnl': 0,
                    'long_positions': 0,
                    'short_positions': 0
                }

            summary['symbols'][pos.symbol]['positions'] += 1
            summary['symbols'][pos.symbol]['unrealized_pnl'] += float(pos.unrealized_pnl)
            summary['symbols'][pos.symbol]['realized_pnl'] += float(pos.realized_pnl)

            if pos.side == 'long':
                summary['symbols'][pos.symbol]['long_positions'] += 1
            else:
                summary['symbols'][pos.symbol]['short_positions'] += 1

        return summary

    def _calculate_risk_metrics(self, positions: List[Position]) -> Dict[str, Any]:
        """Calculate risk metrics for all positions."""
        if not positions:
            return {
                'total_exposure': 0,
                'largest_position': 0,
                'concentration_risk': 0,
                'leverage_ratio': 0
            }

        total_exposure = sum(float(pos.size * pos.current_price) for pos in positions)
        largest_position = max(float(pos.size * pos.current_price) for pos in positions)
        concentration_risk = largest_position / total_exposure if total_exposure > 0 else 0

        total_margin = sum(float(pos.margin) for pos in positions)
        leverage_ratio = total_exposure / total_margin if total_margin > 0 else 0

        return {
            'total_exposure': total_exposure,
            'largest_position': largest_position,
            'concentration_risk': concentration_risk,
            'leverage_ratio': leverage_ratio
        }

    def get_position_history(self, position_id: Optional[str] = None,
                           limit: int = 100) -> List[PositionHistory]:
        """Get position history."""
        history = self.position_history

        if position_id:
            history = [h for h in history if h.position_id == position_id]

        return history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get position manager statistics."""
        self.stats['total_positions'] = len(self.positions)
        self.stats['active_positions'] = len([p for p in self.positions.values() if p.size > 0])

        return {
            **self.stats,
            'total_history_entries': len(self.position_history),
            'is_running': self.is_running
        }

    async def close_position(self, exchange_name: str, symbol: str) -> bool:
        """Close a position (placeholder - would integrate with trading system)."""
        try:
            # This would integrate with the trading execution agent
            # For now, just sync the position status
            await self.sync_exchange_positions(exchange_name)

            position = self.get_position(exchange_name, symbol)
            if position and position.size == Decimal('0'):
                logger.info(f"Position closed: {exchange_name}_{symbol}")
                return True
            else:
                logger.warning(f"Failed to close position: {exchange_name}_{symbol}")
                return False

        except Exception as e:
            logger.error(f"Error closing position {exchange_name}_{symbol}: {e}")
            return False
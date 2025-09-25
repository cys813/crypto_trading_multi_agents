"""
Database models and session management for data collection agent.

This module defines the base database models and session management
for both PostgreSQL (business data) and TimescaleDB (time-series data).
"""

import logging
from typing import Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from ..config.settings import get_settings


# Configure logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create base classes for different databases
Base = declarative_base()
TimescaleBase = declarative_base()

# Database engines
postgres_engine = None
timescaledb_engine = None

# Session factories
PostgresSession = None
TimescaleSession = None


def create_postgres_engine():
    """Create PostgreSQL engine for business data."""
    global postgres_engine

    if postgres_engine is None:
        try:
            postgres_engine = create_engine(
                settings.postgres_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            logger.info("PostgreSQL engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL engine: {e}")
            raise

    return postgres_engine


def create_timescaledb_engine():
    """Create TimescaleDB engine for time-series data."""
    global timescaledb_engine

    if timescaledb_engine is None:
        try:
            timescaledb_engine = create_engine(
                settings.timescaledb_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            logger.info("TimescaleDB engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create TimescaleDB engine: {e}")
            raise

    return timescaledb_engine


def create_session_factories():
    """Create session factories for both databases."""
    global PostgresSession, TimescaleSession

    if PostgresSession is None:
        postgres_engine = create_postgres_engine()
        PostgresSession = sessionmaker(
            bind=postgres_engine,
            autocommit=False,
            autoflush=False
        )
        logger.info("PostgreSQL session factory created")

    if TimescaleSession is None:
        timescaledb_engine = create_timescaledb_engine()
        TimescaleSession = sessionmaker(
            bind=timescaledb_engine,
            autocommit=False,
            autoflush=False
        )
        logger.info("TimescaleDB session factory created")


def get_postgres_session() -> Session:
    """Get a PostgreSQL session."""
    if PostgresSession is None:
        create_session_factories()
    return PostgresSession()


def get_timescaledb_session() -> Session:
    """Get a TimescaleDB session."""
    if TimescaleSession is None:
        create_session_factories()
    return TimescaleSession()


def get_session(database: str = 'postgres') -> Session:
    """Get a database session based on database type."""
    if database == 'postgres':
        return get_postgres_session()
    elif database == 'timescaledb':
        return get_timescaledb_session()
    else:
        raise ValueError(f"Unsupported database type: {database}")


def create_tables():
    """Create all database tables."""
    try:
        # Create PostgreSQL tables
        postgres_engine = create_postgres_engine()
        Base.metadata.create_all(bind=postgres_engine)
        logger.info("PostgreSQL tables created successfully")

        # Create TimescaleDB tables
        timescaledb_engine = create_timescaledb_engine()
        TimescaleBase.metadata.create_all(bind=timescaledb_engine)
        logger.info("TimescaleDB tables created successfully")

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables."""
    try:
        # Drop PostgreSQL tables
        if postgres_engine:
            Base.metadata.drop_all(bind=postgres_engine)
            logger.info("PostgreSQL tables dropped successfully")

        # Drop TimescaleDB tables
        if timescaledb_engine:
            TimescaleBase.metadata.drop_all(bind=timescaledb_engine)
            logger.info("TimescaleDB tables dropped successfully")

    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def close_engines():
    """Close all database engines."""
    try:
        if postgres_engine:
            postgres_engine.dispose()
            logger.info("PostgreSQL engine disposed")

        if timescaledb_engine:
            timescaledb_engine.dispose()
            logger.info("TimescaleDB engine disposed")

    except Exception as e:
        logger.error(f"Error closing database engines: {e}")


class BaseModel:
    """Base model with common functionality."""

    id = UUID(as_uuid=True, primary_key=True, default=uuid.uuid4)
    created_at = datetime.utcnow
    updated_at = datetime.utcnow

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_timestamp(self):
        """Update the timestamp."""
        self.updated_at = datetime.utcnow()

    @classmethod
    def create(cls, session: Session, **kwargs):
        """Create a new record."""
        instance = cls(**kwargs)
        session.add(instance)
        session.commit()
        return instance

    @classmethod
    def get_by_id(cls, session: Session, id: uuid.UUID):
        """Get record by ID."""
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls, session: Session, limit: int = 100, offset: int = 0):
        """Get all records with pagination."""
        return session.query(cls).offset(offset).limit(limit).all()

    def save(self, session: Session):
        """Save the record."""
        self.update_timestamp()
        session.add(self)
        session.commit()

    def delete(self, session: Session):
        """Delete the record."""
        session.delete(self)
        session.commit()


class TimeSeriesBaseModel:
    """Base model for time-series data."""

    timestamp = None  # To be overridden by subclasses
    exchange = None   # To be overridden by subclasses
    symbol = None     # To be overridden by subclasses

    @classmethod
    def get_time_range(cls, session: Session, start_time: datetime, end_time: datetime,
                      exchange: Optional[str] = None, symbol: Optional[str] = None):
        """Get records within time range."""
        query = session.query(cls).filter(
            cls.timestamp >= start_time,
            cls.timestamp <= end_time
        )

        if exchange:
            query = query.filter(cls.exchange == exchange)

        if symbol:
            query = query.filter(cls.symbol == symbol)

        return query.all()

    @classmethod
    def get_latest(cls, session: Session, exchange: str, symbol: str, limit: int = 100):
        """Get latest records for a symbol."""
        return session.query(cls).filter(
            cls.exchange == exchange,
            cls.symbol == symbol
        ).order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def create_timescaledb_hypertable(cls, session: Session):
        """Create TimescaleDB hypertable for time-series data."""
        # This would be implemented with TimescaleDB-specific commands
        # For now, we'll use a placeholder
        pass


# Import all models to ensure they are registered
from .market_data import MarketData, OHLCVData, OrderBookData, TradeData
from .position import Position, PositionHistory
from .order import Order, OrderHistory
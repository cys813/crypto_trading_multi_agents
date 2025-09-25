"""
Main application entry point for the data collection agent.

This module provides the main FastAPI application with all the API routes
and startup/shutdown functionality.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import get_config, config_manager
from .core.logger import get_logger, logger_manager
from .core.monitoring import start_metrics_collection, stop_metrics_collection, get_dashboard_data
from .core.exceptions import error_handler, handle_exceptions, ErrorContext
from .api import market_router, position_router, order_router
from .core.data_collector import DataCollector
from .core.position_manager import PositionManager
from .core.order_manager import OrderManager
from .utils.metrics import MetricsCollector


# Get logger instance
logger = get_logger(__name__)

# Global variables
data_collector = None
position_manager = None
order_manager = None
metrics_collector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Data Collection Agent application")

    # Initialize configuration
    config = get_config()
    logger.info(f"Application loaded in {config.environment} environment")
    logger.info(f"Debug mode: {config.debug}")

    # Initialize components
    global data_collector, position_manager, order_manager, metrics_collector

    try:
        # Start metrics collection
        start_metrics_collection()

        # Initialize metrics collector
        metrics_collector = MetricsCollector()
        await metrics_collector.start_cleanup_task()

        # Initialize data collector
        data_collector = DataCollector()
        await data_collector.start()

        # Initialize position manager
        position_manager = PositionManager()
        await position_manager.start()

        # Initialize order manager
        order_manager = OrderManager()
        await order_manager.start()

        logger.info("All components initialized successfully")

        # Validate configuration
        validation_errors = config_manager.validate_config()
        if validation_errors:
            logger.warning(f"Configuration validation issues: {validation_errors}")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="application",
            operation="startup"
        ))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Data Collection Agent application")

    try:
        # Stop all components
        if order_manager:
            await order_manager.stop()

        if position_manager:
            await position_manager.stop()

        if data_collector:
            await data_collector.stop()

        if metrics_collector:
            await metrics_collector.stop_cleanup_task()

        # Stop metrics collection
        stop_metrics_collection()

        # Cleanup logger resources
        logger_manager.cleanup()

        logger.info("All components stopped successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="application",
            operation="shutdown"
        ))


# Create FastAPI application
app = FastAPI(
    title="Crypto Trading Data Collection Agent",
    description="A comprehensive data collection system for cryptocurrency trading with multi-exchange support",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(market_router)
app.include_router(position_router)
app.include_router(order_router)


# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "components": {
                "data_collector": data_collector is not None,
                "position_manager": position_manager is not None,
                "order_manager": order_manager is not None,
                "metrics_collector": metrics_collector is not None
            }
        }

        # Check if data collector is running
        if data_collector:
            collection_status = data_collector.get_collection_status()
            health_status["data_collection"] = collection_status

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# Root endpoint
@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Crypto Trading Data Collection Agent",
        "version": "1.0.0",
        "description": "A comprehensive data collection system for cryptocurrency trading with multi-exchange support",
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "market_data": "/api/v1/market",
            "positions": "/api/v1/positions",
            "orders": "/api/v1/orders"
        }
    }


# System info endpoint
@app.get("/api/v1/system/info", tags=["system"])
async def system_info():
    """Get system information."""
    config = get_config()

    try:
        # Get component statistics
        data_collection_stats = data_collector.get_collection_status() if data_collector else {}
        position_summary = await position_manager.get_position_summary() if position_manager else {}
        order_summary = await order_manager.get_order_summary() if order_manager else {}

        return {
            "application": {
                "name": config.app_name,
                "version": config.version,
                "environment": config.environment,
                "debug": config.debug,
                "uptime": "N/A"  # Could be calculated from startup time
            },
            "settings": {
                "log_level": config.logging.level,
                "log_format": config.logging.format,
                "api_host": config.host,
                "api_port": config.port,
                "max_concurrent_connections": config.max_concurrent_connections,
                "data_quality_threshold": config.data_quality_threshold,
                "monitoring_enabled": config.monitoring.prometheus_enabled
            },
            "components": {
                "data_collection": data_collection_stats,
                "position_management": position_summary,
                "order_management": order_summary
            },
            "databases": {
                "timescaledb": {
                    "host": config.timescaledb.host,
                    "port": config.timescaledb.port,
                    "database": config.timescaledb.database,
                    "pool_size": config.timescaledb.pool_size
                },
                "postgres": {
                    "host": config.postgresql.host,
                    "port": config.postgresql.port,
                    "database": config.postgresql.database,
                    "pool_size": config.postgresql.pool_size
                },
                "redis": {
                    "host": config.redis.host,
                    "port": config.redis.port,
                    "database": config.redis.database,
                    "pool_size": config.redis.pool_size
                }
            },
            "exchanges": {
                name: {
                    "enabled": exchange_config.enabled,
                    "sandbox": exchange_config.sandbox,
                    "rate_limit": exchange_config.rate_limit
                }
                for name, exchange_config in config.exchanges.items()
            }
        }

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="system_info"
        ))
        raise HTTPException(status_code=500, detail="Failed to get system information")


# Metrics endpoint
@app.get("/api/v1/system/metrics", tags=["system"])
async def get_system_metrics():
    """Get system metrics."""
    try:
        return get_dashboard_data()

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_metrics"
        ))
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


# Configuration reload endpoint
@app.post("/api/v1/system/reload-config", tags=["system"])
async def reload_config():
    """Reload configuration."""
    try:
        new_config = config_manager.reload()

        # Reload logging configuration
        logger_manager.reload_logging()

        return {
            "message": "Configuration reloaded successfully",
            "environment": new_config.environment,
            "debug": new_config.debug,
            "log_level": new_config.logging.level
        }

    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="reload_config"
        ))
        raise HTTPException(status_code=500, detail="Failed to reload configuration")


# Configuration validation endpoint
@app.get("/api/v1/system/config-validation", tags=["system"])
async def validate_config():
    """Validate current configuration."""
    try:
        errors = config_manager.validate_config()

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "config_summary": config_manager.get_environment_config()
        }

    except Exception as e:
        logger.error(f"Failed to validate configuration: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="validate_config"
        ))
        raise HTTPException(status_code=500, detail="Failed to validate configuration")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )


# Development server entry point
def run_dev_server():
    """Run the development server."""
    config = get_config()

    logger.info(f"Starting development server on {config.host}:{config.port}")

    uvicorn.run(
        "src.data_collection.main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level=config.logging.level.lower()
    )


# Production server entry point
def run_prod_server():
    """Run the production server."""
    config = get_config()

    logger.info(f"Starting production server on {config.host}:{config.port}")

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        workers=4,  # Default workers for production
        log_level=config.logging.level.lower()
    )


if __name__ == "__main__":
    # Run development server by default
    run_dev_server()
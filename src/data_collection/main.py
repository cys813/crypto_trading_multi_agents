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

from .config.settings import get_settings
from .api import market_router, position_router, order_router
from .core.data_collector import DataCollector
from .core.position_manager import PositionManager
from .core.order_manager import OrderManager
from .utils.metrics import MetricsCollector


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
data_collector = None
position_manager = None
order_manager = None
metrics_collector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Data Collection Agent application")

    # Initialize settings
    settings = get_settings()
    logger.info(f"Application settings loaded with log level: {settings.LOG_LEVEL}")

    # Initialize components
    global data_collector, position_manager, order_manager, metrics_collector

    try:
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

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
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

        logger.info("All components stopped successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


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
    settings = get_settings()

    try:
        # Get component statistics
        data_collection_stats = data_collector.get_collection_status() if data_collector else {}
        position_summary = await position_manager.get_position_summary() if position_manager else {}
        order_summary = await order_manager.get_order_summary() if order_manager else {}

        return {
            "application": {
                "name": "Crypto Trading Data Collection Agent",
                "version": "1.0.0",
                "uptime": "N/A"  # Could be calculated from startup time
            },
            "settings": {
                "log_level": settings.LOG_LEVEL,
                "api_host": settings.API_HOST,
                "api_port": settings.API_PORT,
                "max_concurrent_connections": settings.MAX_CONCURRENT_CONNECTIONS,
                "data_quality_threshold": settings.DATA_QUALITY_THRESHOLD
            },
            "components": {
                "data_collection": data_collection_stats,
                "position_management": position_summary,
                "order_management": order_summary
            },
            "databases": {
                "postgres": {
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                    "database": settings.POSTGRES_DB
                },
                "timescaledb": {
                    "host": settings.TIMESCALEDB_HOST,
                    "port": settings.TIMESCALEDB_PORT,
                    "database": settings.TIMESCALEDB_DB
                },
                "redis": {
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system information")


# Metrics endpoint
@app.get("/api/v1/system/metrics", tags=["system"])
async def get_system_metrics():
    """Get system metrics."""
    try:
        metrics = {}

        if metrics_collector:
            metrics["system"] = metrics_collector.get_system_metrics()
            metrics["requests"] = metrics_collector.get_request_metrics()
            metrics["data_quality"] = metrics_collector.get_data_quality_metrics()
            metrics["top_errors"] = metrics_collector.get_top_errors()
            metrics["slowest_endpoints"] = metrics_collector.get_slowest_endpoints()

        return metrics

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


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
    settings = get_settings()

    logger.info(f"Starting development server on {settings.API_HOST}:{settings.API_PORT}")

    uvicorn.run(
        "src.data_collection.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )


# Production server entry point
def run_prod_server():
    """Run the production server."""
    settings = get_settings()

    logger.info(f"Starting production server on {settings.API_HOST}:{settings.API_PORT}")

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    # Run development server by default
    run_dev_server()
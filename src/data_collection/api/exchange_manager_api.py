"""
API endpoints for the Enhanced Exchange Manager.

This module provides REST API endpoints for managing and monitoring
the multi-exchange connection system.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.enhanced_exchange_manager import exchange_manager, ExchangeStatus, ConnectionStrategy, Priority
from ..core.exceptions import error_handler, ErrorContext
from ..utils.metrics import metrics_collector
from ..core.logger import get_logger

logger = get_logger(__name__)

# Create router
exchange_router = APIRouter(prefix="/api/v1/exchanges", tags=["exchange-manager"])


# Pydantic models for request/response
class ExchangeStatusResponse(BaseModel):
    """Exchange status response model."""
    exchange_id: str
    status: str
    latency: float
    success_rate: float
    health_score: float
    active_connections: int
    total_requests: int
    error_count: int
    last_ping: float
    region: Optional[str] = None
    capabilities: List[str]


class ExchangeConfigRequest(BaseModel):
    """Exchange configuration request model."""
    enabled: bool = True
    sandbox: bool = False
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    rate_limit: int = 100
    timeout: int = 10000
    enable_rate_limit: bool = True
    weight: int = 100
    options: Dict[str, Any] = Field(default_factory=dict)


class LoadBalanceResponse(BaseModel):
    """Load balancing response model."""
    strategy: str
    available_connections: int
    total_connections: int
    current_load: float
    recommendations: List[str]


class RateLimitResponse(BaseModel):
    """Rate limit response model."""
    exchange_id: str
    method: str
    remaining_requests: int
    limit: int
    window_seconds: int
    reset_time: float


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    overall_health: str
    exchanges_checked: int
    healthy_exchanges: int
    degraded_exchanges: int
    unhealthy_exchanges: int
    details: Dict[str, Any]


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model."""
    timestamp: str
    total_requests: int
    success_rate: float
    average_latency: float
    throughput_rps: float
    error_rate: float
    exchange_metrics: Dict[str, Any]


class ConnectionPoolStatusResponse(BaseModel):
    """Connection pool status response model."""
    exchange_id: str
    pool_size: int
    active_connections: int
    idle_connections: int
    utilization_rate: float
    queue_length: int


# API Endpoints

@exchange_router.get("/status", response_model=Dict[str, ExchangeStatusResponse])
async def get_all_exchanges_status():
    """Get status of all exchanges."""
    try:
        status_data = await exchange_manager.get_exchange_status()
        return status_data

    except Exception as e:
        logger.error(f"Failed to get exchanges status: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_exchanges_status"
        ))
        raise HTTPException(status_code=500, detail="Failed to get exchanges status")


@exchange_router.get("/{exchange_id}/status", response_model=ExchangeStatusResponse)
async def get_exchange_status(exchange_id: str):
    """Get status of a specific exchange."""
    try:
        status_data = await exchange_manager.get_exchange_status(exchange_id)
        if not status_data:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_id} not found")

        return status_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exchange {exchange_id} status: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_exchange_status",
            exchange=exchange_id
        ))
        raise HTTPException(status_code=500, detail="Failed to get exchange status")


@exchange_router.post("/reload")
async def reload_exchange_connections(background_tasks: BackgroundTasks):
    """Reload exchange connections."""
    try:
        # Stop current manager
        await exchange_manager.close()

        # Initialize again
        background_tasks.add_task(exchange_manager.initialize)

        return {"message": "Exchange connections reload initiated"}

    except Exception as e:
        logger.error(f"Failed to reload exchange connections: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="reload_exchanges"
        ))
        raise HTTPException(status_code=500, detail="Failed to reload exchange connections")


@exchange_router.get("/load-balance", response_model=LoadBalanceResponse)
async def get_load_balance_status():
    """Get current load balancing status."""
    try:
        # Get current connections status
        status_data = await exchange_manager.get_exchange_status()

        # Calculate load metrics
        total_connections = sum(conn.get("active_connections", 0) for conn in status_data.values())
        healthy_connections = sum(1 for conn in status_data.values() if conn.get("status") == "healthy")

        current_load = 1.0 - (healthy_connections / max(len(status_data), 1))

        recommendations = []
        if current_load > 0.8:
            recommendations.append("Consider adding more exchange connections")
        if current_load > 0.6:
            recommendations.append("Monitor latency and error rates closely")
        if healthy_connections < len(status_data) * 0.5:
            recommendations.append("Multiple exchanges showing issues - investigate")

        return LoadBalanceResponse(
            strategy=exchange_manager.strategy.value,
            available_connections=healthy_connections,
            total_connections=len(status_data),
            current_load=current_load,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Failed to get load balance status: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_load_balance_status"
        ))
        raise HTTPException(status_code=500, detail="Failed to get load balance status")


@exchange_router.post("/load-balance/strategy")
async def set_load_balance_strategy(strategy: str):
    """Set load balancing strategy."""
    try:
        try:
            new_strategy = ConnectionStrategy(strategy)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")

        exchange_manager.strategy = new_strategy
        return {"message": f"Load balancing strategy changed to {strategy}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set load balance strategy: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="set_load_balance_strategy"
        ))
        raise HTTPException(status_code=500, detail="Failed to set load balance strategy")


@exchange_router.get("/{exchange_id}/rate-limit/{method}", response_model=RateLimitResponse)
async def get_rate_limit_status(exchange_id: str, method: str):
    """Get rate limit status for an exchange method."""
    try:
        if not exchange_manager.rate_limiter:
            raise HTTPException(status_code=503, detail="Rate limiter not available")

        remaining = await exchange_manager.rate_limiter.get_remaining_requests(exchange_id, method)

        return RateLimitResponse(
            exchange_id=exchange_id,
            method=method,
            remaining_requests=remaining,
            limit=100,  # Default limit
            window_seconds=60,
            reset_time=datetime.now().timestamp() + 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_rate_limit_status",
            exchange=exchange_id
        ))
        raise HTTPException(status_code=500, detail="Failed to get rate limit status")


@exchange_router.post("/health-check", response_model=HealthCheckResponse)
async def trigger_health_check(background_tasks: BackgroundTasks):
    """Trigger immediate health check for all exchanges."""
    try:
        # Get current status before health check
        before_status = await exchange_manager.get_exchange_status()

        # Trigger health check
        await exchange_manager._perform_health_checks()

        # Get status after health check
        after_status = await exchange_manager.get_exchange_status()

        # Calculate health summary
        total_exchanges = len(after_status)
        healthy = sum(1 for status in after_status.values() if status.get("status") == "healthy")
        degraded = sum(1 for status in after_status.values() if status.get("status") == "degraded")
        unhealthy = sum(1 for status in after_status.values() if status.get("status") == "unhealthy")

        overall_health = "healthy"
        if unhealthy > 0:
            overall_health = "unhealthy"
        elif degraded > total_exchanges * 0.3:
            overall_health = "degraded"

        return HealthCheckResponse(
            overall_health=overall_health,
            exchanges_checked=total_exchanges,
            healthy_exchanges=healthy,
            degraded_exchanges=degraded,
            unhealthy_exchanges=unhealthy,
            details=after_status
        )

    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="trigger_health_check"
        ))
        raise HTTPException(status_code=500, detail="Failed to trigger health check")


@exchange_router.get("/metrics/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    time_range: int = Query(3600, description="Time range in seconds"),
    exchange_id: Optional[str] = Query(None, description="Filter by exchange ID")
):
    """Get performance metrics for exchanges."""
    try:
        # Calculate time range
        time_delta = timedelta(seconds=time_range)

        # Get request metrics
        request_metrics = metrics_collector.get_request_metrics(
            exchange=exchange_id,
            time_range=time_delta
        )

        # Get exchange-specific metrics
        exchange_metrics = {}
        if exchange_id:
            status = await exchange_manager.get_exchange_status(exchange_id)
            if status:
                exchange_metrics[exchange_id] = status
        else:
            exchange_metrics = await exchange_manager.get_exchange_status()

        # Calculate throughput
        total_requests = request_metrics.get('total_requests', 0)
        throughput_rps = total_requests / max(time_range, 1)

        return PerformanceMetricsResponse(
            timestamp=datetime.now().isoformat(),
            total_requests=total_requests,
            success_rate=request_metrics.get('success_rate', 0),
            average_latency=request_metrics.get('avg_latency', 0),
            throughput_rps=throughput_rps,
            error_rate=request_metrics.get('error_rate', 0),
            exchange_metrics=exchange_metrics
        )

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_performance_metrics"
        ))
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@exchange_router.get("/connection-pool/{exchange_id}", response_model=ConnectionPoolStatusResponse)
async def get_connection_pool_status(exchange_id: str):
    """Get connection pool status for an exchange."""
    try:
        # Get exchange status
        status = await exchange_manager.get_exchange_status(exchange_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_id} not found")

        # Get connection pool information
        pool_info = exchange_manager.connection_pool
        active_connections = pool_info.active_connections.get(exchange_id, 0)
        available_connections = len(pool_info.connections.get(exchange_id, []))

        # Calculate utilization
        total_connections = active_connections + available_connections
        utilization_rate = active_connections / max(total_connections, 1)

        return ConnectionPoolStatusResponse(
            exchange_id=exchange_id,
            pool_size=pool_info.max_size,
            active_connections=active_connections,
            idle_connections=available_connections,
            utilization_rate=utilization_rate,
            queue_length=0  # Could be implemented if needed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection pool status: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_connection_pool_status",
            exchange=exchange_id
        ))
        raise HTTPException(status_code=500, detail="Failed to get connection pool status")


@exchange_router.post("/{exchange_id}/enable")
async def enable_exchange(exchange_id: str):
    """Enable a disabled exchange."""
    try:
        if exchange_id not in exchange_manager.connections:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_id} not found")

        connection = exchange_manager.connections[exchange_id]
        if connection.status == ExchangeStatus.MAINTENANCE:
            connection.status = ExchangeStatus.HEALTHY
            return {"message": f"Exchange {exchange_id} enabled"}
        else:
            return {"message": f"Exchange {exchange_id} is already enabled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable exchange {exchange_id}: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="enable_exchange",
            exchange=exchange_id
        ))
        raise HTTPException(status_code=500, detail="Failed to enable exchange")


@exchange_router.post("/{exchange_id}/disable")
async def disable_exchange(exchange_id: str):
    """Disable an exchange for maintenance."""
    try:
        if exchange_id not in exchange_manager.connections:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_id} not found")

        connection = exchange_manager.connections[exchange_id]
        connection.status = ExchangeStatus.MAINTENANCE
        return {"message": f"Exchange {exchange_id} disabled for maintenance"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable exchange {exchange_id}: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="disable_exchange",
            exchange=exchange_id
        ))
        raise HTTPException(status_code=500, detail="Failed to disable exchange")


@exchange_router.get("/test-connection/{exchange_id}")
async def test_exchange_connection(exchange_id: str):
    """Test connection to a specific exchange."""
    try:
        if exchange_id not in exchange_manager.connections:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_id} not found")

        start_time = datetime.now()
        try:
            # Execute a simple test request
            result = await exchange_manager.execute_request('fetch_time', exchange_id=exchange_id)
            latency = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "exchange_id": exchange_id,
                "status": "connected",
                "latency_ms": latency,
                "timestamp": datetime.now().isoformat(),
                "response_time": result
            }

        except Exception as e:
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "exchange_id": exchange_id,
                "status": "failed",
                "latency_ms": latency,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test exchange connection: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="test_exchange_connection",
            exchange=exchange_id
        ))
        raise HTTPException(status_code=500, detail="Failed to test exchange connection")


@exchange_router.get("/dashboard")
async def get_exchange_manager_dashboard():
    """Get comprehensive dashboard data for exchange manager."""
    try:
        # Get all status data
        status_data = await exchange_manager.get_exchange_status()

        # Get performance metrics
        performance = await get_performance_metrics()

        # Calculate summary statistics
        total_exchanges = len(status_data)
        healthy_exchanges = sum(1 for s in status_data.values() if s.get("status") == "healthy")
        degraded_exchanges = sum(1 for s in status_data.values() if s.get("status") == "degraded")
        unhealthy_exchanges = sum(1 for s in status_data.values() if s.get("status") == "unhealthy")

        # Calculate total metrics
        total_requests = sum(s.get("total_requests", 0) for s in status_data.values())
        total_errors = sum(s.get("error_count", 0) for s in status_data.values())
        avg_latency = sum(s.get("latency", 0) for s in status_data.values()) / max(total_exchanges, 1)

        return {
            "summary": {
                "total_exchanges": total_exchanges,
                "healthy_exchanges": healthy_exchanges,
                "degraded_exchanges": degraded_exchanges,
                "unhealthy_exchanges": unhealthy_exchanges,
                "overall_health": "healthy" if unhealthy_exchanges == 0 else "degraded",
                "load_balancing_strategy": exchange_manager.strategy.value
            },
            "performance": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_success_rate": 1.0 - (total_errors / max(total_requests, 1)),
                "average_latency": avg_latency,
                "throughput_rps": performance.throughput_rps
            },
            "exchanges": status_data,
            "alerts": [],
            "recommendations": []
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        error_handler.handle_exception(e, ErrorContext(
            component="api",
            operation="get_exchange_manager_dashboard"
        ))
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")
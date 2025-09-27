"""
Metrics collector for gathering system metrics
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics
import logging

from .models import (
    PerformanceMetrics,
    QualityMetrics,
    HealthMetrics,
    BusinessMetrics,
    ResourceUsage,
    ConcurrencyStats,
    SignalQualityMetrics,
    LLMQualityMetrics,
    DataQualityMetrics,
    ServiceHealth,
    DataSourceHealth,
    ComponentHealth,
    HealthStatus,
    BusinessMetrics
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Metrics collector for gathering system metrics"""

    def __init__(self, collector_type: str, config):
        """
        Initialize metrics collector

        Args:
            collector_type: Type of collector (performance, quality, health, business)
            config: Monitoring configuration
        """
        self.collector_type = collector_type
        self.config = config

        # Track active requests for concurrency
        self.active_requests = {}
        self.request_history = []
        self.performance_history = []

        # Business metrics tracking
        self.signal_history = []
        self.report_history = []

    async def collect_performance_metrics(self) -> PerformanceMetrics:
        """
        Collect performance metrics

        Returns:
            Performance metrics
        """
        start_time = time.time()

        try:
            # Collect resource usage
            resource_usage = await self._collect_resource_usage()

            # Collect concurrency stats
            concurrency_stats = await self._collect_concurrency_stats()

            # Collect processing times
            processing_times = await self._collect_processing_times()

            # Collect throughput
            throughput = await self._collect_throughput()

            # Create performance metrics
            performance_metrics = PerformanceMetrics(
                data_processing_latency=processing_times.get('data_processing', 0),
                indicator_calculation_time=processing_times.get('indicator_calculation', 0),
                llm_response_time=processing_times.get('llm_response', 0),
                report_generation_time=processing_times.get('report_generation', 0),
                throughput_requests_per_second=throughput,
                resource_usage=resource_usage,
                concurrency_stats=concurrency_stats,
                timestamp=datetime.now()
            )

            # Store in history
            self.performance_history.append(performance_metrics)

            collection_time = time.time() - start_time
            logger.debug(f"Collected performance metrics in {collection_time:.3f}s")

            return performance_metrics

        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            # Return default metrics
            return PerformanceMetrics(
                data_processing_latency=0,
                indicator_calculation_time=0,
                llm_response_time=0,
                report_generation_time=0,
                throughput_requests_per_second=0,
                resource_usage=ResourceUsage(0, 0, 0, 0, 0, datetime.now()),
                concurrency_stats=ConcurrencyStats(0, 0, 0, 0, 0, datetime.now()),
                timestamp=datetime.now()
            )

    async def collect_quality_metrics(self) -> QualityMetrics:
        """
        Collect quality metrics

        Returns:
            Quality metrics
        """
        try:
            # Collect signal quality metrics
            signal_quality = await self._collect_signal_quality_metrics()

            # Collect LLM quality metrics
            llm_quality = await self._collect_llm_quality_metrics()

            # Collect data quality metrics
            data_quality = await self._collect_data_quality_metrics()

            quality_metrics = QualityMetrics(
                signal_quality=signal_quality,
                llm_quality=llm_quality,
                data_quality=data_quality,
                timestamp=datetime.now()
            )

            logger.debug("Collected quality metrics")

            return quality_metrics

        except Exception as e:
            logger.error(f"Error collecting quality metrics: {e}")
            # Return default metrics
            return QualityMetrics(
                signal_quality=SignalQualityMetrics(0, 0, 0, 0, datetime.now()),
                llm_quality=LLMQualityMetrics(0, 0, 0, 0, 0, datetime.now()),
                data_quality=DataQualityMetrics(0, 0, 0, 0, datetime.now()),
                timestamp=datetime.now()
            )

    async def collect_health_metrics(self) -> HealthMetrics:
        """
        Collect health metrics

        Returns:
            Health metrics
        """
        try:
            # Check services health
            services_health = await self._check_services_health()

            # Check data sources health
            data_sources_health = await self._check_data_sources_health()

            # Check components health
            components_health = await self._check_components_health()

            # Calculate overall status
            overall_status = self._calculate_overall_health_status(
                services_health, data_sources_health, components_health
            )

            # Calculate uptime
            uptime_percentage = self._calculate_uptime_percentage()

            health_metrics = HealthMetrics(
                overall_status=overall_status,
                services_health=services_health,
                data_sources_health=data_sources_health,
                components_health=components_health,
                uptime_percentage=uptime_percentage,
                timestamp=datetime.now()
            )

            logger.debug("Collected health metrics")

            return health_metrics

        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
            # Return default metrics
            return HealthMetrics(
                overall_status=HealthStatus.UNHEALTHY,
                services_health={},
                data_sources_health={},
                components_health={},
                uptime_percentage=0,
                timestamp=datetime.now()
            )

    async def collect_business_metrics(self) -> BusinessMetrics:
        """
        Collect business metrics

        Returns:
            Business metrics
        """
        try:
            # Calculate signal metrics
            total_signals = len(self.signal_history)
            successful_signals = len([s for s in self.signal_history if s.get('success', False)])

            # Calculate average confidence
            avg_confidence = 0
            if self.signal_history:
                confidences = [s.get('confidence', 0) for s in self.signal_history]
                avg_confidence = statistics.mean(confidences)

            # Calculate report metrics
            total_reports = len(self.report_history)

            # Calculate user satisfaction (placeholder)
            user_satisfaction = 0.85  # Default satisfaction score

            business_metrics = BusinessMetrics(
                total_signals_generated=total_signals,
                successful_signals=successful_signals,
                average_signal_confidence=avg_confidence,
                total_reports_generated=total_reports,
                user_satisfaction_score=user_satisfaction,
                timestamp=datetime.now()
            )

            logger.debug("Collected business metrics")

            return business_metrics

        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            return BusinessMetrics(0, 0, 0, 0, 0, datetime.now())

    async def _collect_resource_usage(self) -> ResourceUsage:
        """Collect system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network I/O
            network = psutil.net_io_counters()
            network_io_bytes = network.bytes_sent + network.bytes_recv

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_bytes = disk_io.read_bytes + disk_io.write_bytes

            return ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_bytes=network_io_bytes,
                disk_io_bytes=disk_io_bytes,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error collecting resource usage: {e}")
            return ResourceUsage(0, 0, 0, 0, 0, datetime.now())

    async def _collect_concurrency_stats(self) -> ConcurrencyStats:
        """Collect concurrency statistics"""
        try:
            # Get current active requests
            active_count = len(self.active_requests)

            # Calculate max concurrent
            max_concurrent = max(self._get_max_concurrent_history(), active_count)

            # Calculate total requests
            total_requests = len(self.request_history)

            # Calculate average response time
            avg_response_time = self._calculate_average_response_time()

            # Calculate error rate
            error_rate = self._calculate_error_rate()

            return ConcurrencyStats(
                active_requests=active_count,
                max_concurrent=max_concurrent,
                total_requests=total_requests,
                average_response_time=avg_response_time,
                error_rate=error_rate,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error collecting concurrency stats: {e}")
            return ConcurrencyStats(0, 0, 0, 0, 0, datetime.now())

    async def _collect_processing_times(self) -> Dict[str, float]:
        """Collect processing times for different operations"""
        processing_times = {}

        try:
            # Get recent processing times from history
            if self.performance_history:
                recent_metrics = self.performance_history[-10:]  # Last 10 measurements

                processing_times['data_processing'] = statistics.mean([
                    m.data_processing_latency for m in recent_metrics
                ])

                processing_times['indicator_calculation'] = statistics.mean([
                    m.indicator_calculation_time for m in recent_metrics
                ])

                processing_times['llm_response'] = statistics.mean([
                    m.llm_response_time for m in recent_metrics
                ])

                processing_times['report_generation'] = statistics.mean([
                    m.report_generation_time for m in recent_metrics
                ])

            else:
                # Default values
                processing_times = {
                    'data_processing': 0.1,
                    'indicator_calculation': 0.05,
                    'llm_response': 1.0,
                    'report_generation': 0.5
                }

        except Exception as e:
            logger.error(f"Error collecting processing times: {e}")
            processing_times = {key: 0.0 for key in ['data_processing', 'indicator_calculation', 'llm_response', 'report_generation']}

        return processing_times

    async def _collect_throughput(self) -> float:
        """Collect system throughput"""
        try:
            # Calculate requests per second in the last minute
            cutoff_time = datetime.now() - timedelta(minutes=1)
            recent_requests = [r for r in self.request_history if r['end_time'] > cutoff_time]

            if len(recent_requests) < 2:
                return 0.0

            # Calculate throughput
            time_span = (recent_requests[-1]['end_time'] - recent_requests[0]['start_time']).total_seconds()
            if time_span > 0:
                return len(recent_requests) / time_span

            return 0.0

        except Exception as e:
            logger.error(f"Error collecting throughput: {e}")
            return 0.0

    async def _collect_signal_quality_metrics(self) -> SignalQualityMetrics:
        """Collect signal quality metrics"""
        try:
            # This would typically calculate actual signal quality metrics
            # For now, we'll use placeholder calculations

            # Signal accuracy (placeholder)
            signal_accuracy = 0.85

            # False positive rate (placeholder)
            false_positive_rate = 0.15

            # Signal coverage (placeholder)
            signal_coverage = 0.92

            # Signal consistency (placeholder)
            signal_consistency = 0.88

            return SignalQualityMetrics(
                signal_accuracy=signal_accuracy,
                false_positive_rate=false_positive_rate,
                signal_coverage=signal_coverage,
                signal_consistency=signal_consistency,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error collecting signal quality metrics: {e}")
            return SignalQualityMetrics(0, 0, 0, 0, datetime.now())

    async def _collect_llm_quality_metrics(self) -> LLMQualityMetrics:
        """Collect LLM quality metrics"""
        try:
            # Response quality score (placeholder)
            response_quality_score = 0.82

            # Average response time (placeholder)
            response_time_avg = 1.2

            # Error rate (placeholder)
            error_rate = 0.05

            # Cost per request (placeholder)
            cost_per_request = 0.002

            # Cache hit rate (placeholder)
            cache_hit_rate = 0.75

            return LLMQualityMetrics(
                response_quality_score=response_quality_score,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                cost_per_request=cost_per_request,
                cache_hit_rate=cache_hit_rate,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error collecting LLM quality metrics: {e}")
            return LLMQualityMetrics(0, 0, 0, 0, 0, datetime.now())

    async def _collect_data_quality_metrics(self) -> DataQualityMetrics:
        """Collect data quality metrics"""
        try:
            # Completeness score (placeholder)
            completeness_score = 0.95

            # Accuracy score (placeholder)
            accuracy_score = 0.92

            # Timeliness score (placeholder)
            timeliness_score = 0.98

            # Consistency score (placeholder)
            consistency_score = 0.90

            return DataQualityMetrics(
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                timeliness_score=timeliness_score,
                consistency_score=consistency_score,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error collecting data quality metrics: {e}")
            return DataQualityMetrics(0, 0, 0, 0, datetime.now())

    async def _check_services_health(self) -> Dict[str, ServiceHealth]:
        """Check health of various services"""
        services_health = {}

        try:
            # Check data collection service
            services_health['data_collection'] = await self._check_service_health(
                'data_collection', 'http://localhost:8000/health'
            )

            # Check LLM service
            services_health['llm_service'] = await self._check_service_health(
                'llm_service', 'http://localhost:8001/health'
            )

            # Check report generation service
            services_health['report_service'] = await self._check_service_health(
                'report_service', 'http://localhost:8002/health'
            )

        except Exception as e:
            logger.error(f"Error checking services health: {e}")

        return services_health

    async def _check_data_sources_health(self) -> Dict[str, DataSourceHealth]:
        """Check health of data sources"""
        data_sources_health = {}

        try:
            # Check Binance API
            data_sources_health['binance'] = DataSourceHealth(
                source_name='binance',
                is_available=True,
                latency=0.05,
                error_rate=0.01,
                last_update=datetime.now()
            )

            # Check CoinGecko API
            data_sources_health['coingecko'] = DataSourceHealth(
                source_name='coingecko',
                is_available=True,
                latency=0.08,
                error_rate=0.02,
                last_update=datetime.now()
            )

            # Check news sources
            data_sources_health['news_sources'] = DataSourceHealth(
                source_name='news_sources',
                is_available=True,
                latency=0.12,
                error_rate=0.05,
                last_update=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error checking data sources health: {e}")

        return data_sources_health

    async def _check_components_health(self) -> Dict[str, ComponentHealth]:
        """Check health of system components"""
        components_health = {}

        try:
            # Check technical analysis component
            components_health['technical_analysis'] = ComponentHealth(
                component_name='technical_analysis',
                status=HealthStatus.HEALTHY,
                health_score=0.95,
                issues=[],
                last_check=datetime.now()
            )

            # Check signal recognition component
            components_health['signal_recognition'] = ComponentHealth(
                component_name='signal_recognition',
                status=HealthStatus.HEALTHY,
                health_score=0.92,
                issues=[],
                last_check=datetime.now()
            )

            # Check report generation component
            components_health['report_generation'] = ComponentHealth(
                component_name='report_generation',
                status=HealthStatus.HEALTHY,
                health_score=0.88,
                issues=[],
                last_check=datetime.now()
            )

            # Check monitoring component
            components_health['monitoring'] = ComponentHealth(
                component_name='monitoring',
                status=HealthStatus.HEALTHY,
                health_score=1.0,
                issues=[],
                last_check=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error checking components health: {e}")

        return components_health

    async def _check_service_health(self, service_name: str, health_url: str) -> ServiceHealth:
        """Check health of a specific service"""
        try:
            # In a real implementation, this would make HTTP requests
            # For now, we'll simulate healthy services
            return ServiceHealth(
                service_name=service_name,
                is_healthy=True,
                response_time=0.05,
                last_check=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error checking service {service_name}: {e}")
            return ServiceHealth(
                service_name=service_name,
                is_healthy=False,
                response_time=0,
                error_message=str(e),
                last_check=datetime.now()
            )

    def _calculate_overall_health_status(self, services_health: Dict[str, ServiceHealth],
                                       data_sources_health: Dict[str, DataSourceHealth],
                                       components_health: Dict[str, ComponentHealth]) -> HealthStatus:
        """Calculate overall system health status"""
        try:
            # Count unhealthy components
            unhealthy_services = sum(1 for s in services_health.values() if not s.is_healthy)
            unhealthy_sources = sum(1 for s in data_sources_health.values() if not s.is_available)
            unhealthy_components = sum(1 for c in components_health.values() if c.status != HealthStatus.HEALTHY)

            total_components = len(services_health) + len(data_sources_health) + len(components_health)
            unhealthy_count = unhealthy_services + unhealthy_sources + unhealthy_components

            # Determine overall status
            if unhealthy_count == 0:
                return HealthStatus.HEALTHY
            elif unhealthy_count / total_components < 0.1:
                return HealthStatus.WARNING
            elif unhealthy_count / total_components < 0.3:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.UNHEALTHY

        except Exception as e:
            logger.error(f"Error calculating overall health status: {e}")
            return HealthStatus.UNHEALTHY

    def _calculate_uptime_percentage(self) -> float:
        """Calculate system uptime percentage"""
        try:
            # This would typically be calculated from actual uptime data
            # For now, we'll return a high uptime percentage
            return 0.999  # 99.9% uptime

        except Exception as e:
            logger.error(f"Error calculating uptime: {e}")
            return 0.0

    def _get_max_concurrent_history(self) -> List[int]:
        """Get maximum concurrent requests history"""
        # This would track historical max concurrent values
        return [len(self.active_requests)]

    def _calculate_average_response_time(self) -> float:
        """Calculate average response time"""
        try:
            if not self.request_history:
                return 0.0

            response_times = []
            for request in self.request_history:
                if 'response_time' in request:
                    response_times.append(request['response_time'])

            return statistics.mean(response_times) if response_times else 0.0

        except Exception as e:
            logger.error(f"Error calculating average response time: {e}")
            return 0.0

    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        try:
            if not self.request_history:
                return 0.0

            error_count = sum(1 for r in self.request_history if r.get('error', False))
            return error_count / len(self.request_history)

        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0

    def track_request_start(self, request_id: str):
        """Track the start of a request"""
        self.active_requests[request_id] = {
            'start_time': datetime.now(),
            'request_id': request_id
        }

    def track_request_end(self, request_id: str, response_time: float = None, error: bool = False):
        """Track the end of a request"""
        if request_id in self.active_requests:
            request_data = self.active_requests.pop(request_id)
            request_data['end_time'] = datetime.now()
            request_data['response_time'] = response_time or (request_data['end_time'] - request_data['start_time']).total_seconds()
            request_data['error'] = error

            self.request_history.append(request_data)

            # Keep only recent history (last 1000 requests)
            if len(self.request_history) > 1000:
                self.request_history = self.request_history[-1000:]

    def track_signal(self, signal_data: Dict[str, Any]):
        """Track signal generation"""
        self.signal_history.append({
            'timestamp': datetime.now(),
            **signal_data
        })

        # Keep only recent history (last 1000 signals)
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]

    def track_report(self, report_data: Dict[str, Any]):
        """Track report generation"""
        self.report_history.append({
            'timestamp': datetime.now(),
            **report_data
        })

        # Keep only recent history (last 1000 reports)
        if len(self.report_history) > 1000:
            self.report_history = self.report_history[-1000:]

    def get_recent_metrics(self, metric_type: str, duration: timedelta) -> List[Any]:
        """Get recent metrics of a specific type"""
        cutoff_time = datetime.now() - duration

        if metric_type == 'performance':
            return [m for m in self.performance_history if m.timestamp > cutoff_time]
        elif metric_type == 'quality':
            return []  # Would return quality metrics history
        elif metric_type == 'health':
            return []  # Would return health metrics history
        elif metric_type == 'business':
            return []  # Would return business metrics history
        else:
            return []
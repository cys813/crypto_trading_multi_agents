"""
Health evaluator for assessing system health
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics
import logging

from .models import (
    HealthStatus,
    SystemMetrics,
    ServiceHealth,
    DataSourceHealth,
    ComponentHealth,
    MonitoringConfig
)

logger = logging.getLogger(__name__)


class HealthEvaluator:
    """Health evaluator for assessing system health"""

    def __init__(self, config: MonitoringConfig):
        """
        Initialize health evaluator

        Args:
            config: Monitoring configuration
        """
        self.config = config

        # Health rules and thresholds
        self.health_rules = self._load_health_rules()

        # Historical health data
        self.health_history = []

    def _load_health_rules(self) -> Dict[str, Any]:
        """Load health evaluation rules"""
        return {
            'performance': {
                'max_latency_ms': self.config.max_latency_ms * 1000,
                'max_error_rate': self.config.max_error_rate,
                'min_throughput': 1.0,  # requests per second
                'max_cpu_percent': 80,
                'max_memory_percent': 85,
                'max_disk_percent': 90
            },
            'quality': {
                'min_signal_accuracy': 0.7,
                'max_false_positive_rate': 0.3,
                'min_data_completeness': 0.8,
                'min_llm_quality': 0.6
            },
            'availability': {
                'min_uptime': self.config.min_availability,
                'max_service_downtime': timedelta(minutes=5),
                'max_data_source_latency': 2.0  # seconds
            }
        }

    async def evaluate_system_health(self, metrics: SystemMetrics) -> HealthStatus:
        """
        Evaluate overall system health

        Args:
            metrics: Current system metrics

        Returns:
            Overall health status
        """
        try:
            # Evaluate different aspects of health
            performance_health = await self._evaluate_performance_health(metrics)
            quality_health = await self._evaluate_quality_health(metrics)
            availability_health = await self._evaluate_availability_health(metrics)

            # Combine health assessments
            overall_health = self._combine_health_assessments(
                performance_health, quality_health, availability_health
            )

            # Store in history
            self.health_history.append({
                'timestamp': datetime.now(),
                'overall_status': overall_health,
                'performance_health': performance_health,
                'quality_health': quality_health,
                'availability_health': availability_health,
                'metrics': metrics
            })

            # Keep only recent history
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-1000:]

            logger.debug(f"System health evaluation: {overall_health}")

            return overall_health

        except Exception as e:
            logger.error(f"Error evaluating system health: {e}")
            return HealthStatus.UNHEALTHY

    async def evaluate_component_health(self, component: str, component_metrics: Dict[str, Any]) -> ComponentHealth:
        """
        Evaluate health of a specific component

        Args:
            component: Component name
            component_metrics: Component-specific metrics

        Returns:
            Component health status
        """
        try:
            # Component-specific health evaluation logic
            health_score = self._calculate_component_health_score(component, component_metrics)
            status = self._determine_component_status(health_score)
            issues = self._identify_component_issues(component, component_metrics)

            return ComponentHealth(
                component_name=component,
                status=status,
                health_score=health_score,
                issues=issues,
                last_check=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error evaluating component {component} health: {e}")
            return ComponentHealth(
                component_name=component,
                status=HealthStatus.UNHEALTHY,
                health_score=0.0,
                issues=[f"Evaluation error: {str(e)}"],
                last_check=datetime.now()
            )

    async def evaluate_data_quality(self, quality_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate data quality

        Args:
            quality_metrics: Quality metrics data

        Returns:
            Data quality evaluation results
        """
        try:
            evaluation = {
                'overall_score': 0.0,
                'completeness': {'score': 0.0, 'status': 'unknown'},
                'accuracy': {'score': 0.0, 'status': 'unknown'},
                'timeliness': {'score': 0.0, 'status': 'unknown'},
                'consistency': {'score': 0.0, 'status': 'unknown'},
                'recommendations': []
            }

            # Evaluate completeness
            completeness_score = quality_metrics.get('completeness_score', 0)
            evaluation['completeness']['score'] = completeness_score
            evaluation['completeness']['status'] = self._get_quality_status(completeness_score)

            # Evaluate accuracy
            accuracy_score = quality_metrics.get('accuracy_score', 0)
            evaluation['accuracy']['score'] = accuracy_score
            evaluation['accuracy']['status'] = self._get_quality_status(accuracy_score)

            # Evaluate timeliness
            timeliness_score = quality_metrics.get('timeliness_score', 0)
            evaluation['timeliness']['score'] = timeliness_score
            evaluation['timeliness']['status'] = self._get_quality_status(timeliness_score)

            # Evaluate consistency
            consistency_score = quality_metrics.get('consistency_score', 0)
            evaluation['consistency']['score'] = consistency_score
            evaluation['consistency']['status'] = self._get_quality_status(consistency_score)

            # Calculate overall score
            scores = [
                completeness_score,
                accuracy_score,
                timeliness_score,
                consistency_score
            ]
            evaluation['overall_score'] = statistics.mean(scores)

            # Generate recommendations
            evaluation['recommendations'] = self._generate_data_quality_recommendations(evaluation)

            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating data quality: {e}")
            return {
                'overall_score': 0.0,
                'error': str(e),
                'recommendations': ['Error in data quality evaluation']
            }

    async def _evaluate_performance_health(self, metrics: SystemMetrics) -> HealthStatus:
        """Evaluate performance health"""
        performance = metrics.performance
        rules = self.health_rules['performance']

        issues = []

        # Check latency
        if performance.data_processing_latency > rules['max_latency_ms'] / 1000:
            issues.append(f"High processing latency: {performance.data_processing_latency * 1000:.1f}ms")

        # Check error rate
        if performance.concurrency_stats.error_rate > rules['max_error_rate']:
            issues.append(f"High error rate: {performance.concurrency_stats.error_rate:.1%}")

        # Check throughput
        if performance.throughput_requests_per_second < rules['min_throughput']:
            issues.append(f"Low throughput: {performance.throughput_requests_per_second:.1f} req/s")

        # Check resource usage
        if performance.resource_usage.cpu_percent > rules['max_cpu_percent']:
            issues.append(f"High CPU usage: {performance.resource_usage.cpu_percent:.1f}%")

        if performance.resource_usage.memory_percent > rules['max_memory_percent']:
            issues.append(f"High memory usage: {performance.resource_usage.memory_percent:.1f}%")

        if performance.resource_usage.disk_percent > rules['max_disk_percent']:
            issues.append(f"High disk usage: {performance.resource_usage.disk_percent:.1f}%")

        # Determine health status
        if len(issues) == 0:
            return HealthStatus.HEALTHY
        elif len(issues) <= 1:
            return HealthStatus.WARNING
        elif len(issues) <= 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    async def _evaluate_quality_health(self, metrics: SystemMetrics) -> HealthStatus:
        """Evaluate quality health"""
        quality = metrics.quality
        rules = self.health_rules['quality']

        issues = []

        # Check signal quality
        if quality.signal_quality.signal_accuracy < rules['min_signal_accuracy']:
            issues.append(f"Low signal accuracy: {quality.signal_quality.signal_accuracy:.1%}")

        if quality.signal_quality.false_positive_rate > rules['max_false_positive_rate']:
            issues.append(f"High false positive rate: {quality.signal_quality.false_positive_rate:.1%}")

        # Check data quality
        if quality.data_quality.completeness_score < rules['min_data_completeness']:
            issues.append(f"Low data completeness: {quality.data_quality.completeness_score:.1%}")

        # Check LLM quality
        if quality.llm_quality.response_quality_score < rules['min_llm_quality']:
            issues.append(f"Low LLM response quality: {quality.llm_quality.response_quality_score:.1%}")

        # Determine health status
        if len(issues) == 0:
            return HealthStatus.HEALTHY
        elif len(issues) <= 1:
            return HealthStatus.WARNING
        elif len(issues) <= 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    async def _evaluate_availability_health(self, metrics: SystemMetrics) -> HealthStatus:
        """Evaluate availability health"""
        health = metrics.health
        rules = self.health_rules['availability']

        issues = []

        # Check overall uptime
        if health.uptime_percentage < rules['min_uptime']:
            issues.append(f"Low uptime: {health.uptime_percentage:.1%}")

        # Check services health
        unhealthy_services = [name for name, service in health.services_health.items() if not service.is_healthy]
        if unhealthy_services:
            issues.append(f"Unhealthy services: {', '.join(unhealthy_services)}")

        # Check data sources
        unavailable_sources = [name for name, source in health.data_sources_health.items() if not source.is_available]
        if unavailable_sources:
            issues.append(f"Unavailable data sources: {', '.join(unavailable_sources)}")

        # Check data source latency
        high_latency_sources = [
            name for name, source in health.data_sources_health.items()
            if source.is_available and source.latency > rules['max_data_source_latency']
        ]
        if high_latency_sources:
            issues.append(f"High latency data sources: {', '.join(high_latency_sources)}")

        # Check components health
        unhealthy_components = [
            name for name, component in health.components_health.items()
            if component.status != HealthStatus.HEALTHY
        ]
        if unhealthy_components:
            issues.append(f"Degraded components: {', '.join(unhealthy_components)}")

        # Determine health status
        if len(issues) == 0:
            return HealthStatus.HEALTHY
        elif len(issues) <= 1:
            return HealthStatus.WARNING
        elif len(issues) <= 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def _combine_health_assessments(self, performance_health: HealthStatus,
                                   quality_health: HealthStatus,
                                   availability_health: HealthStatus) -> HealthStatus:
        """Combine multiple health assessments into overall status"""
        # Priority order: UNHEALTHY > DEGRADED > WARNING > HEALTHY
        health_statuses = [performance_health, quality_health, availability_health]

        if HealthStatus.UNHEALTHY in health_statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in health_statuses:
            return HealthStatus.DEGRADED
        elif HealthStatus.WARNING in health_statuses:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _calculate_component_health_score(self, component: str, metrics: Dict[str, Any]) -> float:
        """Calculate health score for a specific component"""
        # Component-specific health calculation logic
        base_score = 1.0

        # Apply penalties based on metrics
        if 'error_rate' in metrics:
            error_rate = metrics['error_rate']
            base_score *= (1 - error_rate)

        if 'response_time' in metrics:
            response_time = metrics['response_time']
            if response_time > 1.0:  # More than 1 second
                base_score *= 0.9
            if response_time > 5.0:  # More than 5 seconds
                base_score *= 0.7

        if 'memory_usage' in metrics:
            memory_usage = metrics['memory_usage']
            if memory_usage > 80:
                base_score *= 0.8
            if memory_usage > 90:
                base_score *= 0.6

        return max(0.0, min(1.0, base_score))

    def _determine_component_status(self, health_score: float) -> HealthStatus:
        """Determine component status based on health score"""
        if health_score >= 0.9:
            return HealthStatus.HEALTHY
        elif health_score >= 0.7:
            return HealthStatus.WARNING
        elif health_score >= 0.5:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def _identify_component_issues(self, component: str, metrics: Dict[str, Any]) -> List[str]:
        """Identify issues with a specific component"""
        issues = []

        if 'error_rate' in metrics and metrics['error_rate'] > 0.05:
            issues.append(f"High error rate: {metrics['error_rate']:.1%}")

        if 'response_time' in metrics and metrics['response_time'] > 2.0:
            issues.append(f"Slow response time: {metrics['response_time']:.1f}s")

        if 'memory_usage' in metrics and metrics['memory_usage'] > 85:
            issues.append(f"High memory usage: {metrics['memory_usage']:.1f}%")

        if not issues:
            issues.append("No issues detected")

        return issues

    def _get_quality_status(self, score: float) -> str:
        """Get quality status based on score"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "fair"
        elif score >= 0.6:
            return "poor"
        else:
            return "critical"

    def _generate_data_quality_recommendations(self, evaluation: Dict[str, Any]) -> List[str]:
        """Generate data quality improvement recommendations"""
        recommendations = []

        # Completeness recommendations
        if evaluation['completeness']['score'] < 0.8:
            recommendations.append("Improve data collection completeness by identifying missing data sources")

        # Accuracy recommendations
        if evaluation['accuracy']['score'] < 0.8:
            recommendations.append("Implement data validation and cleansing procedures")

        # Timeliness recommendations
        if evaluation['timeliness']['score'] < 0.8:
            recommendations.append("Optimize data pipeline for faster processing")

        # Consistency recommendations
        if evaluation['consistency']['score'] < 0.8:
            recommendations.append("Standardize data formats and validation rules")

        if not recommendations:
            recommendations.append("Data quality is within acceptable parameters")

        return recommendations

    def get_health_trends(self, duration: timedelta = None) -> Dict[str, Any]:
        """
        Get health trends over time

        Args:
            duration: Time duration to analyze

        Returns:
            Health trend analysis
        """
        if duration is None:
            duration = timedelta(hours=24)

        cutoff_time = datetime.now() - duration
        recent_health = [h for h in self.health_history if h['timestamp'] > cutoff_time]

        if not recent_health:
            return {'error': 'No health history available'}

        trends = {
            'overall_status_distribution': {},
            'performance_issues': [],
            'quality_issues': [],
            'availability_issues': [],
            'improvement_suggestions': []
        }

        # Analyze status distribution
        status_counts = {}
        for health in recent_health:
            status = health['overall_status']
            status_counts[status] = status_counts.get(status, 0) + 1

        trends['overall_status_distribution'] = status_counts

        # Identify common issues
        for health in recent_health:
            if health['performance_health'] != HealthStatus.HEALTHY:
                trends['performance_issues'].append('Performance degradation detected')

            if health['quality_health'] != HealthStatus.HEALTHY:
                trends['quality_issues'].append('Quality issues detected')

            if health['availability_health'] != HealthStatus.HEALTHY:
                trends['availability_issues'].append('Availability issues detected')

        # Generate improvement suggestions
        trends['improvement_suggestions'] = self._generate_health_improvement_suggestions(trends)

        return trends

    def _generate_health_improvement_suggestions(self, trends: Dict[str, Any]) -> List[str]:
        """Generate health improvement suggestions"""
        suggestions = []

        # Performance suggestions
        if trends['performance_issues']:
            suggestions.append("Consider optimizing system performance and resource usage")

        # Quality suggestions
        if trends['quality_issues']:
            suggestions.append("Review and improve data quality and signal accuracy")

        # Availability suggestions
        if trends['availability_issues']:
            suggestions.append("Improve system reliability and implement better fault tolerance")

        # Overall suggestions
        status_dist = trends['overall_status_distribution']
        total_checks = sum(status_dist.values())
        if total_checks > 0:
            healthy_percentage = status_dist.get(HealthStatus.HEALTHY, 0) / total_checks
            if healthy_percentage < 0.9:
                suggestions.append("Implement comprehensive monitoring and alerting system")

        return suggestions if suggestions else ["System health is within acceptable parameters"]

    def get_component_health_summary(self) -> Dict[str, Any]:
        """Get summary of component health"""
        if not self.health_history:
            return {'error': 'No health history available'}

        latest_health = self.health_history[-1]
        metrics = latest_health['metrics']

        summary = {
            'services': {},
            'data_sources': {},
            'components': {},
            'overall_status': latest_health['overall_status'].value,
            'timestamp': latest_health['timestamp'].isoformat()
        }

        # Services summary
        for name, service in metrics.health.services_health.items():
            summary['services'][name] = {
                'healthy': service.is_healthy,
                'response_time': service.response_time,
                'last_check': service.last_check.isoformat()
            }

        # Data sources summary
        for name, source in metrics.health.data_sources_health.items():
            summary['data_sources'][name] = {
                'available': source.is_available,
                'latency': source.latency,
                'error_rate': source.error_rate,
                'last_update': source.last_update.isoformat()
            }

        # Components summary
        for name, component in metrics.health.components_health.items():
            summary['components'][name] = {
                'status': component.status.value,
                'health_score': component.health_score,
                'issues': component.issues,
                'last_check': component.last_check.isoformat()
            }

        return summary
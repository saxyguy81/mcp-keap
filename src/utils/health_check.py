"""
Health check utilities for Keap MCP service.
Provides comprehensive health monitoring for production deployment.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.utils.logging_utils import get_logger, get_performance_logger


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class ComponentHealth:
    """Health status of a system component."""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    last_check: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: str
    response_time_ms: float
    components: List[ComponentHealth]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        result['components'] = [comp.to_dict() for comp in self.components]
        return result


class HealthChecker:
    """Comprehensive health check system for Keap MCP service."""
    
    def __init__(
        self,
        api_service: Optional[KeapApiService] = None,
        cache_manager: Optional[CacheManager] = None,
        timeout: float = 5.0
    ):
        self.api_service = api_service
        self.cache_manager = cache_manager
        self.timeout = timeout
        self.logger = get_logger("health_check")
        self.performance_logger = get_performance_logger()
        
        # Health check history for trend analysis
        self._check_history: List[SystemHealth] = []
        self._max_history = 100
    
    async def check_system_health(self) -> SystemHealth:
        """
        Perform comprehensive system health check.
        
        Returns:
            SystemHealth object with overall status and component details
        """
        start_time = time.time()
        components = []
        
        # Check all components
        components.append(await self._check_api_connectivity())
        components.append(await self._check_cache_health())
        components.append(await self._check_system_resources())
        components.append(await self._check_performance_metrics())
        
        # Determine overall system status
        overall_status = self._determine_overall_status(components)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        system_health = SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            response_time_ms=response_time_ms,
            components=components,
            metadata={
                "version": "1.0.0",
                "environment": "production",
                "check_duration_ms": response_time_ms
            }
        )
        
        # Store in history
        self._add_to_history(system_health)
        
        # Log health check result
        self.logger.info(
            f"Health check completed: {overall_status.value}",
            extra={
                "structured_data": {
                    "health_status": overall_status.value,
                    "response_time_ms": response_time_ms,
                    "component_count": len(components),
                    "healthy_components": len([c for c in components if c.status == HealthStatus.HEALTHY])
                }
            }
        )
        
        return system_health
    
    async def _check_api_connectivity(self) -> ComponentHealth:
        """Check Keap API connectivity and response."""
        start_time = time.time()
        
        try:
            if not self.api_service:
                return ComponentHealth(
                    name="keap_api",
                    status=HealthStatus.DEGRADED,
                    error_message="API service not configured",
                    last_check=datetime.utcnow().isoformat() + "Z"
                )
            
            # Test API connectivity with a simple request
            # Using asyncio.wait_for for timeout handling
            async def api_test():
                # Simple API call to test connectivity
                response = await self.api_service.get("/contacts", params={"limit": 1})
                return response
            
            response = await asyncio.wait_for(api_test(), timeout=self.timeout)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Check response validity
            if response and isinstance(response, dict):
                status = HealthStatus.HEALTHY
                error_message = None
                details = {
                    "response_received": True,
                    "response_type": type(response).__name__
                }
            else:
                status = HealthStatus.DEGRADED
                error_message = "Invalid API response format"
                details = {"response_received": False}
            
            return ComponentHealth(
                name="keap_api",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=error_message,
                details=details
            )
            
        except asyncio.TimeoutError:
            return ComponentHealth(
                name="keap_api",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=f"API request timeout after {self.timeout}s",
                details={"timeout": True}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="keap_api",
                status=HealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=str(e),
                details={"error_type": type(e).__name__}
            )
    
    async def _check_cache_health(self) -> ComponentHealth:
        """Check cache system health and performance."""
        start_time = time.time()
        
        try:
            if not self.cache_manager:
                return ComponentHealth(
                    name="cache_system",
                    status=HealthStatus.DEGRADED,
                    error_message="Cache manager not configured",
                    last_check=datetime.utcnow().isoformat() + "Z"
                )
            
            # Test cache operations
            test_key = "health_check_test"
            test_value = {"timestamp": time.time(), "data": "test"}
            
            # Test cache write
            await self.cache_manager.set(test_key, test_value, ttl=60)
            
            # Test cache read
            retrieved_value = await self.cache_manager.get(test_key)
            
            # Test cache delete
            await self.cache_manager.delete(test_key)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Validate cache operations
            if retrieved_value == test_value:
                status = HealthStatus.HEALTHY
                error_message = None
            else:
                status = HealthStatus.DEGRADED
                error_message = "Cache read/write mismatch"
            
            # Get cache statistics
            cache_stats = getattr(self.cache_manager, 'get_stats', lambda: {})()
            
            return ComponentHealth(
                name="cache_system",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=error_message,
                details={
                    "operations_tested": ["set", "get", "delete"],
                    "cache_stats": cache_stats
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="cache_system",
                status=HealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=str(e),
                details={"error_type": type(e).__name__}
            )
    
    async def _check_system_resources(self) -> ComponentHealth:
        """Check system resource utilization."""
        start_time = time.time()
        
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            warnings = []
            
            if cpu_percent > 80:
                status = HealthStatus.DEGRADED
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                status = HealthStatus.DEGRADED
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = HealthStatus.CRITICAL
                warnings.append(f"Low disk space: {disk.percent}% used")
            
            error_message = "; ".join(warnings) if warnings else None
            
            return ComponentHealth(
                name="system_resources",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=error_message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except ImportError:
            # psutil not available, use basic checks
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.DEGRADED,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message="System monitoring not available (psutil not installed)",
                details={"monitoring_available": False}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=str(e),
                details={"error_type": type(e).__name__}
            )
    
    async def _check_performance_metrics(self) -> ComponentHealth:
        """Check recent performance metrics and trends."""
        start_time = time.time()
        
        try:
            # Get performance summary from performance monitor
            if hasattr(self.performance_logger, 'get_performance_summary'):
                summary = self.performance_logger.get_performance_summary()
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Analyze performance metrics
                status = HealthStatus.HEALTHY
                warnings = []
                
                # Check error rate
                if hasattr(summary, 'error_rate') and summary.error_rate > 0.05:  # 5%
                    status = HealthStatus.DEGRADED
                    warnings.append(f"High error rate: {summary.error_rate:.2%}")
                
                # Check response time
                if hasattr(summary, 'avg_response_time_ms') and summary.avg_response_time_ms > 3000:  # 3s
                    status = HealthStatus.DEGRADED
                    warnings.append(f"High response time: {summary.avg_response_time_ms:.0f}ms")
                
                # Check cache hit ratio
                if hasattr(summary, 'cache_hit_ratio') and summary.cache_hit_ratio < 0.7:  # 70%
                    status = HealthStatus.DEGRADED
                    warnings.append(f"Low cache hit ratio: {summary.cache_hit_ratio:.1%}")
                
                error_message = "; ".join(warnings) if warnings else None
                
                details = {
                    "performance_monitoring": True,
                    "metrics_available": True
                }
                
                # Add available metrics to details
                for attr in ['error_rate', 'avg_response_time_ms', 'cache_hit_ratio', 'total_requests']:
                    if hasattr(summary, attr):
                        details[attr] = getattr(summary, attr)
                
                return ComponentHealth(
                    name="performance_metrics",
                    status=status,
                    response_time_ms=response_time_ms,
                    last_check=datetime.utcnow().isoformat() + "Z",
                    error_message=error_message,
                    details=details
                )
            else:
                return ComponentHealth(
                    name="performance_metrics",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=datetime.utcnow().isoformat() + "Z",
                    error_message="Performance monitoring not available",
                    details={"performance_monitoring": False}
                )
                
        except Exception as e:
            return ComponentHealth(
                name="performance_metrics",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat() + "Z",
                error_message=str(e),
                details={"error_type": type(e).__name__}
            )
    
    def _determine_overall_status(self, components: List[ComponentHealth]) -> HealthStatus:
        """Determine overall system status based on component health."""
        if not components:
            return HealthStatus.CRITICAL
        
        # Count component statuses
        status_counts = {}
        for component in components:
            status = component.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine overall status based on worst component status
        if HealthStatus.CRITICAL in status_counts:
            return HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in status_counts:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in status_counts:
            # If more than half are degraded, system is unhealthy
            if status_counts[HealthStatus.DEGRADED] > len(components) / 2:
                return HealthStatus.UNHEALTHY
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _add_to_history(self, health_status: SystemHealth):
        """Add health check result to history."""
        self._check_history.append(health_status)
        
        # Maintain history size limit
        if len(self._check_history) > self._max_history:
            self._check_history = self._check_history[-self._max_history:]
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_iso = cutoff_time.isoformat() + "Z"
        
        # Filter history by time
        recent_checks = [
            check for check in self._check_history
            if check.timestamp >= cutoff_iso
        ]
        
        if not recent_checks:
            return {"error": "No health data available for specified period"}
        
        # Calculate trends
        status_distribution = {}
        avg_response_time = 0
        component_availability = {}
        
        for check in recent_checks:
            # Status distribution
            status = check.status.value
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Average response time
            avg_response_time += check.response_time_ms
            
            # Component availability
            for component in check.components:
                comp_name = component.name
                if comp_name not in component_availability:
                    component_availability[comp_name] = {"healthy": 0, "total": 0}
                
                component_availability[comp_name]["total"] += 1
                if component.status == HealthStatus.HEALTHY:
                    component_availability[comp_name]["healthy"] += 1
        
        avg_response_time /= len(recent_checks)
        
        # Calculate availability percentages
        for comp_name, stats in component_availability.items():
            stats["availability_percent"] = (stats["healthy"] / stats["total"]) * 100
        
        return {
            "period_hours": hours,
            "total_checks": len(recent_checks),
            "status_distribution": status_distribution,
            "average_response_time_ms": avg_response_time,
            "component_availability": component_availability,
            "latest_check": recent_checks[-1].to_dict() if recent_checks else None
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker(
    api_service: Optional[KeapApiService] = None,
    cache_manager: Optional[CacheManager] = None
) -> HealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(api_service, cache_manager)
    return _health_checker


async def health_check() -> Dict[str, Any]:
    """Simple health check function for external use."""
    checker = get_health_checker()
    health = await checker.check_system_health()
    return health.to_dict()


async def readiness_check() -> Dict[str, Any]:
    """Readiness check for Kubernetes/container orchestration."""
    checker = get_health_checker()
    health = await checker.check_system_health()
    
    # For readiness, we're more strict - degraded components might still be "ready"
    ready = health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    return {
        "ready": ready,
        "status": health.status.value,
        "timestamp": health.timestamp,
        "checks": len(health.components)
    }


async def liveness_check() -> Dict[str, Any]:
    """Liveness check for Kubernetes/container orchestration."""
    try:
        # Simple check - just ensure the service can respond
        start_time = time.time()
        
        # Basic responsiveness test
        await asyncio.sleep(0.001)  # Minimal async operation
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": response_time_ms
        }
    except Exception as e:
        return {
            "alive": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
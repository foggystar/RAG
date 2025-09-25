"""
Health check and monitoring utilities for the RAG system.
Provides comprehensive health checks, metrics, and system monitoring.
"""

import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel
import structlog
from utils.middleware import logger, REQUEST_COUNT, QUERIES_PROCESSED, PDF_UPLOADS, ERROR_COUNT
from utils.cache import cache_manager
from utils.error_handling import RAGException, ErrorCode
from rag_modules import get_database
from config import server_settings, Config

logger = structlog.get_logger()


class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Individual component health status"""
    name: str
    status: str
    message: str
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class SystemHealth(BaseModel):
    """Overall system health status"""
    status: str
    timestamp: datetime
    uptime: float
    components: List[ComponentHealth]
    metrics: Dict[str, Any]
    version: str = "1.0.0"


class HealthChecker:
    """Health checker for system components"""
    
    def __init__(self):
        self.start_time = time.time()
    
    async def check_database(self) -> ComponentHealth:
        """Check database connectivity and health"""
        start_time = time.time()
        
        try:
            # Test database connection
            client = get_database.get_database_client()
            collections = client.list_collections()
            
            response_time = time.time() - start_time
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message=f"Database connected successfully. Collections: {len(collections)}",
                response_time=response_time,
                details={
                    "collections_count": len(collections),
                    "collection_names": collections[:5] if collections else []  # Show first 5
                }
            )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("Database health check failed", error=str(e))
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    async def check_cache(self) -> ComponentHealth:
        """Check Redis cache connectivity"""
        start_time = time.time()
        
        try:
            if cache_manager._is_available():
                stats = cache_manager.get_cache_stats()
                response_time = time.time() - start_time
                
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.HEALTHY,
                    message="Redis cache connected",
                    response_time=response_time,
                    details=stats
                )
            else:
                response_time = time.time() - start_time
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.DEGRADED,
                    message="Redis cache not available (caching disabled)",
                    response_time=response_time
                )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("Cache health check failed", error=str(e))
            
            return ComponentHealth(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                message=f"Cache check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    async def check_file_system(self) -> ComponentHealth:
        """Check file system accessibility"""
        start_time = time.time()
        
        try:
            import os
            
            # Check required directories
            required_dirs = ["uploads", "static", "docs", "database"]
            accessible_dirs = []
            
            for dir_name in required_dirs:
                if os.path.exists(dir_name) and os.access(dir_name, os.W_OK):
                    accessible_dirs.append(dir_name)
            
            response_time = time.time() - start_time
            
            if len(accessible_dirs) == len(required_dirs):
                return ComponentHealth(
                    name="file_system",
                    status=HealthStatus.HEALTHY,
                    message=f"All required directories accessible: {accessible_dirs}",
                    response_time=response_time,
                    details={"accessible_dirs": accessible_dirs}
                )
            else:
                missing_dirs = set(required_dirs) - set(accessible_dirs)
                return ComponentHealth(
                    name="file_system",
                    status=HealthStatus.DEGRADED,
                    message=f"Missing directories: {missing_dirs}",
                    response_time=response_time,
                    details={
                        "accessible_dirs": accessible_dirs,
                        "missing_dirs": list(missing_dirs)
                    }
                )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("File system health check failed", error=str(e))
            
            return ComponentHealth(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                message=f"File system check failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    async def check_api_connectivity(self) -> ComponentHealth:
        """Check external API connectivity"""
        start_time = time.time()
        
        try:
            import httpx
            
            # Test API connectivity with a simple request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{Config.API_BASE_URL}/models")
                
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return ComponentHealth(
                    name="api_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="External API connected successfully",
                    response_time=response_time,
                    details={"status_code": response.status_code}
                )
            else:
                return ComponentHealth(
                    name="api_connectivity",
                    status=HealthStatus.DEGRADED,
                    message=f"API returned status {response.status_code}",
                    response_time=response_time,
                    details={"status_code": response.status_code}
                )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("API connectivity check failed", error=str(e))
            
            return ComponentHealth(
                name="api_connectivity",
                status=HealthStatus.DEGRADED,
                message=f"API connectivity failed: {str(e)}",
                response_time=response_time,
                details={"error": str(e)}
            )
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process information
            process = psutil.Process()
            process_info = {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_rss": process.memory_info().rss,
                "threads": process.num_threads(),
                "open_files": len(process.open_files())
            }
            
            # Get Prometheus metrics
            prometheus_metrics = self._get_prometheus_metrics()
            
            return {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count()
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "process": process_info,
                "prometheus": prometheus_metrics
            }
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {"error": str(e)}
    
    def _get_prometheus_metrics(self) -> Dict[str, Any]:
        """Get Prometheus metrics summary"""
        try:
            from prometheus_client import REGISTRY
            
            metrics_summary = {}
            
            for metric in REGISTRY._collector_to_names:
                for name in REGISTRY._collector_to_names[metric]:
                    if name in ['rag_http_requests_total', 'rag_queries_processed_total', 'rag_pdf_uploads_total', 'rag_errors_total']:
                        try:
                            samples = list(metric.collect())[0].samples
                            total = sum(sample.value for sample in samples)
                            metrics_summary[name] = total
                        except Exception:
                            continue
            
            return metrics_summary
        except Exception as e:
            logger.error("Failed to get Prometheus metrics", error=str(e))
            return {}
    
    async def check_health(self) -> SystemHealth:
        """Perform comprehensive health check"""
        start_time = time.time()
        
        # Check all components
        components = await asyncio.gather(
            self.check_database(),
            self.check_cache(),
            self.check_file_system(),
            self.check_api_connectivity(),
            return_exceptions=True
        )
        
        # Process results
        healthy_components = []
        degraded_components = []
        unhealthy_components = []
        
        for component in components:
            if isinstance(component, Exception):
                logger.error("Health check exception", error=str(component))
                unhealthy_components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(component)}"
                ))
            elif component.status == HealthStatus.HEALTHY:
                healthy_components.append(component)
            elif component.status == HealthStatus.DEGRADED:
                degraded_components.append(component)
            else:
                unhealthy_components.append(component)
        
        # Determine overall status
        if unhealthy_components:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_components:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get system metrics
        metrics = await self.get_system_metrics()
        
        total_time = time.time() - start_time
        
        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            uptime=time.time() - self.start_time,
            components=healthy_components + degraded_components + unhealthy_components,
            metrics=metrics
        )


# Global health checker instance
health_checker = HealthChecker()


class HealthMonitor:
    """Continuous health monitoring"""
    
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self.is_running = False
        self.last_health_check = None
        self.health_history = []
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self.is_running = True
        logger.info("Health monitoring started", interval_seconds=self.interval)
        
        while self.is_running:
            try:
                health = await health_checker.check_health()
                self.last_health_check = health
                
                # Keep health history (last 100 checks)
                self.health_history.append(health)
                if len(self.health_history) > 100:
                    self.health_history.pop(0)
                
                # Log if there are issues
                if health.status != HealthStatus.HEALTHY:
                    logger.warning(
                        "Health check detected issues",
                        status=health.status,
                        unhealthy_components=[c.name for c in health.components if c.status == HealthStatus.UNHEALTHY]
                    )
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(self.interval)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_running = False
        logger.info("Health monitoring stopped")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health monitoring summary"""
        if not self.health_history:
            return {"message": "No health checks performed yet"}
        
        recent_checks = self.health_history[-10:]  # Last 10 checks
        
        return {
            "last_check": self.last_health_check.timestamp if self.last_health_check else None,
            "total_checks": len(self.health_history),
            "recent_status_distribution": {
                "healthy": sum(1 for h in recent_checks if h.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for h in recent_checks if h.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for h in recent_checks if h.status == HealthStatus.UNHEALTHY)
            },
            "current_status": self.last_health_check.status if self.last_health_check else "unknown"
        }


# Global health monitor instance
health_monitor = HealthMonitor()
"""
Production Monitoring and Metrics System
本番環境向け監視・メトリクス システム
"""

import os
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class CircuitBreakerState(Enum):
    """Circuit Breaker状態"""
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"


@dataclass
class HealthStatus:
    """システムヘルス状態"""
    component: str
    status: str  # healthy, unhealthy, degraded
    last_check: datetime
    response_time_ms: float
    error_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """
    Circuit Breaker実装
    本番環境での障害伝播防止
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        
        self.logger = logging.getLogger(__name__)
    
    async def call(self, func: Callable, *args, **kwargs):
        """Circuit Breaker経由での関数呼び出し"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """リセット試行すべきかを判定"""
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """成功時の処理"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class PrometheusMetrics:
    """Prometheus メトリクス管理"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        if not PROMETHEUS_AVAILABLE:
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Prometheus client not available - metrics disabled")
            return
        
        # Memory System メトリクス
        self.memory_operations_total = Counter(
            'discord_agent_memory_operations_total',
            'Total memory operations',
            ['operation_type', 'status'],
            registry=self.registry
        )
        
        self.memory_operation_duration = Histogram(
            'discord_agent_memory_operation_duration_seconds',
            'Memory operation duration',
            ['operation_type'],
            registry=self.registry
        )
        
        # Discord メトリクス
        self.discord_messages_total = Counter(
            'discord_agent_messages_total',
            'Total Discord messages processed',
            ['message_type', 'agent'],
            registry=self.registry
        )
        
        self.discord_response_time = Histogram(
            'discord_agent_response_time_seconds',
            'Discord response time',
            ['agent'],
            registry=self.registry
        )
        
        # Gemini API メトリクス
        self.gemini_api_calls_total = Counter(
            'discord_agent_gemini_api_calls_total',
            'Total Gemini API calls',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.gemini_api_duration = Histogram(
            'discord_agent_gemini_api_duration_seconds',
            'Gemini API call duration',
            ['operation'],
            registry=self.registry
        )
        
        # システムメトリクス
        self.active_connections = Gauge(
            'discord_agent_active_connections',
            'Active connections',
            ['connection_type'],
            registry=self.registry
        )
        
        self.system_errors_total = Counter(
            'discord_agent_system_errors_total',
            'Total system errors',
            ['error_type', 'component'],
            registry=self.registry
        )
    
    def record_memory_operation(self, operation_type: str, duration: float, status: str = "success"):
        """メモリ操作のメトリクス記録"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.memory_operations_total.labels(operation_type=operation_type, status=status).inc()
        self.memory_operation_duration.labels(operation_type=operation_type).observe(duration)
    
    def record_discord_message(self, message_type: str, agent: str, response_time: float):
        """Discordメッセージのメトリクス記録"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.discord_messages_total.labels(message_type=message_type, agent=agent).inc()
        self.discord_response_time.labels(agent=agent).observe(response_time)
    
    def record_gemini_api_call(self, operation: str, duration: float, status: str = "success"):
        """Gemini API呼び出しのメトリクス記録"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.gemini_api_calls_total.labels(operation=operation, status=status).inc()
        self.gemini_api_duration.labels(operation=operation).observe(duration)
    
    def set_active_connections(self, connection_type: str, count: int):
        """アクティブ接続数設定"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.active_connections.labels(connection_type=connection_type).set(count)
    
    def record_system_error(self, error_type: str, component: str):
        """システムエラー記録"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.system_errors_total.labels(error_type=error_type, component=component).inc()
    
    def get_metrics(self) -> str:
        """Prometheusメトリクス出力"""
        if not PROMETHEUS_AVAILABLE:
            return ""
        return generate_latest(self.registry).decode('utf-8')


class HealthChecker:
    """ヘルスチェック機能"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthStatus] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_check(self, name: str, check_func: Callable):
        """ヘルスチェック関数を登録"""
        self.checks[name] = check_func
    
    async def run_check(self, name: str) -> HealthStatus:
        """個別ヘルスチェック実行"""
        if name not in self.checks:
            return HealthStatus(
                component=name,
                status="unknown",
                last_check=datetime.now(),
                response_time_ms=0,
                details={"error": "Check function not found"}
            )
        
        start_time = time.time()
        try:
            check_func = self.checks[name]
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus(
                component=name,
                status="healthy" if result.get("healthy", False) else "unhealthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                details=result
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus(
                component=name,
                status="unhealthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_count=1,
                details={"error": str(e)}
            )
            self.logger.error(f"Health check failed for {name}: {e}")
        
        self.last_results[name] = status
        return status
    
    async def run_all_checks(self) -> Dict[str, HealthStatus]:
        """全ヘルスチェック実行"""
        results = {}
        for name in self.checks:
            results[name] = await self.run_check(name)
        return results
    
    def get_overall_status(self) -> Dict[str, Any]:
        """全体ステータス取得"""
        if not self.last_results:
            return {"status": "unknown", "components": {}}
        
        all_healthy = all(
            result.status == "healthy" 
            for result in self.last_results.values()
        )
        
        any_degraded = any(
            result.status == "degraded"
            for result in self.last_results.values()
        )
        
        if all_healthy:
            overall_status = "healthy"
        elif any_degraded:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                name: {
                    "status": result.status,
                    "response_time_ms": result.response_time_ms,
                    "last_check": result.last_check.isoformat(),
                    "details": result.details
                }
                for name, result in self.last_results.items()
            }
        }


class PerformanceMonitor:
    """パフォーマンス監視"""
    
    def __init__(self):
        self.metrics = PrometheusMetrics()
        self.health_checker = HealthChecker()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # パフォーマンス閾値
        self.thresholds = {
            "hot_memory_ms": int(os.getenv('HOT_MEMORY_TARGET_MS', 100)),
            "cold_memory_ms": int(os.getenv('COLD_MEMORY_TARGET_MS', 3000)),
            "embedding_ms": int(os.getenv('EMBEDDING_TARGET_MS', 2000)),
            "error_rate": float(os.getenv('ERROR_RATE_THRESHOLD', 0.05))
        }
        
        self.logger = logging.getLogger(__name__)
    
    def create_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Circuit Breaker作成"""
        cb = CircuitBreaker(**kwargs)
        self.circuit_breakers[name] = cb
        return cb
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Circuit Breaker取得"""
        return self.circuit_breakers.get(name)
    
    async def record_operation(self, 
                              operation_type: str, 
                              component: str,
                              func: Callable,
                              *args, **kwargs):
        """操作実行とメトリクス記録"""
        start_time = time.time()
        status = "success"
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            status = "error"
            self.metrics.record_system_error(type(e).__name__, component)
            raise
            
        finally:
            duration = time.time() - start_time
            self.metrics.record_memory_operation(operation_type, duration, status)
            
            # 閾値チェック
            if component == "memory" and operation_type == "hot_read":
                if duration * 1000 > self.thresholds["hot_memory_ms"]:
                    self.logger.warning(f"Hot memory operation exceeded threshold: {duration*1000:.2f}ms")
    
    def setup_health_checks(self, memory_system, discord_clients):
        """ヘルスチェック設定"""
        
        async def check_redis():
            try:
                if memory_system and memory_system.redis:
                    await memory_system.redis.ping()
                    return {"healthy": True, "latency_ms": "< 5"}
                return {"healthy": False, "error": "Redis not connected"}
            except Exception as e:
                return {"healthy": False, "error": str(e)}
        
        async def check_postgres():
            try:
                if memory_system and memory_system.postgres_pool:
                    async with memory_system.postgres_pool.acquire() as conn:
                        await conn.fetchval('SELECT 1')
                    return {"healthy": True, "pool_size": "active"}
                return {"healthy": False, "error": "PostgreSQL not connected"}
            except Exception as e:
                return {"healthy": False, "error": str(e)}
        
        def check_discord():
            try:
                healthy_clients = 0
                total_clients = len(discord_clients) if discord_clients else 0
                
                for client in discord_clients or []:
                    if hasattr(client, 'is_ready') and client.is_ready():
                        healthy_clients += 1
                
                if total_clients == 0:
                    return {"healthy": False, "error": "No Discord clients configured"}
                
                return {
                    "healthy": healthy_clients == total_clients,
                    "healthy_clients": healthy_clients,
                    "total_clients": total_clients
                }
            except Exception as e:
                return {"healthy": False, "error": str(e)}
        
        self.health_checker.register_check("redis", check_redis)
        self.health_checker.register_check("postgres", check_postgres)
        self.health_checker.register_check("discord", check_discord)
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート取得"""
        health_status = await self.health_checker.run_all_checks()
        overall_status = self.health_checker.get_overall_status()
        
        circuit_breaker_status = {
            name: {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time
            }
            for name, cb in self.circuit_breakers.items()
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_status,
            "circuit_breakers": circuit_breaker_status,
            "thresholds": self.thresholds,
            "metrics_available": PROMETHEUS_AVAILABLE
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Decorator for monitoring functions
def monitor_performance(operation_type: str, component: str):
    """パフォーマンス監視デコレータ"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            return await performance_monitor.record_operation(
                operation_type, component, func, *args, **kwargs
            )
        
        def sync_wrapper(*args, **kwargs):
            import asyncio
            return asyncio.run(performance_monitor.record_operation(
                operation_type, component, func, *args, **kwargs
            ))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
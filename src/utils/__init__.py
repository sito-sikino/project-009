"""
Utilities Module - Clean Architecture
ユーティリティ層モジュール
"""

# Logger module exports
from .logger import (
    # Main logger functions
    setup_logging,
    get_logger,
    get_agent_logger,
    get_performance_logger,
    
    # Manager class
    LoggerManager,
    get_log_manager,
    
    # Specialized formatters
    ColoredFormatter,
    AgentLoggerAdapter,
    
    # Convenience logging functions
    log_function_call,
    log_performance,
    log_error_with_context,
    log_agent_action,
    log_system_startup,
    log_system_shutdown,
    log_component_status
)

# Health monitoring exports (existing) - Temporarily disabled for Phase 7
_HEALTH_AVAILABLE = False
_MONITORING_AVAILABLE = False

# Note: health and monitoring modules will be re-enabled in Phase 8
# when main.py integration is completed

# Export list
__all__ = [
    # Logger exports
    'setup_logging',
    'get_logger',
    'get_agent_logger', 
    'get_performance_logger',
    'LoggerManager',
    'get_log_manager',
    'ColoredFormatter',
    'AgentLoggerAdapter',
    'log_function_call',
    'log_performance',
    'log_error_with_context',
    'log_agent_action',
    'log_system_startup',
    'log_system_shutdown',
    'log_component_status'
]

# Conditional exports
if _HEALTH_AVAILABLE:
    __all__.extend([
        'setup_health_monitoring',
        'HealthStatus',
        'ComponentStatus'
    ])

if _MONITORING_AVAILABLE:
    __all__.extend([
        'performance_monitor',
        'monitor_performance', 
        'PerformanceMetrics'
    ])
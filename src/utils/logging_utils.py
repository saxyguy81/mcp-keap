"""
Enhanced logging utilities for Keap MCP service with structured logging,
performance monitoring, and production-ready configuration.
"""

import json
import logging
import logging.handlers
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict
import os


@dataclass
class LogEntry:
    """Structured log entry for consistent logging format."""
    timestamp: str
    level: str
    message: str
    service: str = "keap-mcp"
    component: Optional[str] = None
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization."""
        entry = asdict(self)
        # Remove None values to keep logs clean
        return {k: v for k, v in entry.items() if v is not None}


class StructuredFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Extract structured data from record
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "keap-mcp",
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any additional structured data
        if hasattr(record, 'structured_data'):
            log_data.update(record.structured_data)
        
        return json.dumps(log_data, default=str)


class PerformanceLogger:
    """Logger for performance metrics and monitoring."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._active_operations: Dict[str, float] = {}
    
    @contextmanager
    def track_operation(self, operation_name: str, **metadata):
        """Context manager for tracking operation performance."""
        start_time = time.time()
        operation_id = f"{operation_name}_{int(start_time * 1000)}"
        
        try:
            self._active_operations[operation_id] = start_time
            self.logger.info(
                f"Operation started: {operation_name}",
                extra={
                    "structured_data": {
                        "operation": operation_name,
                        "operation_id": operation_id,
                        "status": "started",
                        **metadata
                    }
                }
            )
            yield operation_id
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Operation failed: {operation_name}",
                extra={
                    "structured_data": {
                        "operation": operation_name,
                        "operation_id": operation_id,
                        "status": "failed",
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        **metadata
                    }
                }
            )
            raise
            
        finally:
            if operation_id in self._active_operations:
                duration_ms = (time.time() - self._active_operations.pop(operation_id)) * 1000
                self.logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        "structured_data": {
                            "operation": operation_name,
                            "operation_id": operation_id,
                            "status": "completed",
                            "duration_ms": duration_ms,
                            **metadata
                        }
                    }
                )
    
    def log_metric(self, metric_name: str, value: Union[int, float], unit: str = "", **metadata):
        """Log a performance metric."""
        self.logger.info(
            f"Metric: {metric_name}",
            extra={
                "structured_data": {
                    "metric_name": metric_name,
                    "metric_value": value,
                    "metric_unit": unit,
                    "metric_type": "gauge",
                    **metadata
                }
            }
        )
    
    def log_counter(self, counter_name: str, increment: int = 1, **metadata):
        """Log a counter metric."""
        self.logger.info(
            f"Counter: {counter_name}",
            extra={
                "structured_data": {
                    "counter_name": counter_name,
                    "counter_increment": increment,
                    "metric_type": "counter",
                    **metadata
                }
            }
        )


class LoggingConfig:
    """Configuration for logging system."""
    
    def __init__(
        self,
        level: str = "INFO",
        format_type: str = "json",  # "json" or "text"
        log_file: Optional[str] = None,
        rotation_size: str = "100MB",
        retention_days: int = 30,
        console_output: bool = True,
        structured_logging: bool = True
    ):
        self.level = level.upper()
        self.format_type = format_type
        self.log_file = log_file
        self.rotation_size = rotation_size
        self.retention_days = retention_days
        self.console_output = console_output
        self.structured_logging = structured_logging


def setup_logging(config: Optional[LoggingConfig] = None) -> tuple[logging.Logger, PerformanceLogger]:
    """
    Set up comprehensive logging for the Keap MCP service.
    
    Args:
        config: Logging configuration options
        
    Returns:
        Tuple of (main_logger, performance_logger)
    """
    if config is None:
        config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format_type=os.getenv("LOG_FORMAT", "json"),
            log_file=os.getenv("LOG_FILE"),
            console_output=True,
            structured_logging=os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Set up formatters
    if config.format_type == "json" and config.structured_logging:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, config.level))
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.log_file:
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse rotation size
        size_bytes = _parse_size(config.rotation_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_file,
            maxBytes=size_bytes,
            backupCount=config.retention_days,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, config.level))
        root_logger.addHandler(file_handler)
    
    # Create service-specific logger
    service_logger = logging.getLogger("keap-mcp")
    performance_logger = PerformanceLogger(service_logger)
    
    # Log configuration
    service_logger.info(
        "Logging system initialized",
        extra={
            "structured_data": {
                "log_level": config.level,
                "log_format": config.format_type,
                "log_file": config.log_file,
                "structured_logging": config.structured_logging,
                "console_output": config.console_output
            }
        }
    )
    
    return service_logger, performance_logger


def _parse_size(size_str: str) -> int:
    """Parse size string like '100MB' to bytes."""
    size_str = size_str.upper().strip()
    
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4
    }
    
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number = size_str[:-len(suffix)].strip()
            try:
                return int(float(number) * multiplier)
            except ValueError:
                break
    
    # Default to 100MB if parsing fails
    return 100 * 1024 * 1024


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with consistent configuration."""
    return logging.getLogger(f"keap-mcp.{name}")


class SecurityLogger:
    """Specialized logger for security events and audit trails."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_api_access(self, endpoint: str, method: str, user_id: Optional[str] = None, **metadata):
        """Log API access for security monitoring."""
        self.logger.info(
            f"API Access: {method} {endpoint}",
            extra={
                "structured_data": {
                    "event_type": "api_access",
                    "endpoint": endpoint,
                    "method": method,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata
                }
            }
        )
    
    def log_authentication_event(self, event_type: str, success: bool, user_id: Optional[str] = None, **metadata):
        """Log authentication events."""
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"Authentication {event_type}: {'SUCCESS' if success else 'FAILURE'}",
            extra={
                "structured_data": {
                    "event_type": "authentication",
                    "auth_event": event_type,
                    "success": success,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata
                }
            }
        )
    
    def log_rate_limit_event(self, user_id: Optional[str] = None, endpoint: Optional[str] = None, **metadata):
        """Log rate limiting events."""
        self.logger.warning(
            "Rate limit exceeded",
            extra={
                "structured_data": {
                    "event_type": "rate_limit",
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata
                }
            }
        )
    
    def log_error_event(self, error_type: str, error_message: str, **metadata):
        """Log security-relevant errors."""
        self.logger.error(
            f"Security Error: {error_type}",
            extra={
                "structured_data": {
                    "event_type": "security_error",
                    "error_type": error_type,
                    "error_message": error_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata
                }
            }
        )


# Global logger instances (initialized when first imported)
_main_logger: Optional[logging.Logger] = None
_performance_logger: Optional[PerformanceLogger] = None
_security_logger: Optional[SecurityLogger] = None


def get_main_logger() -> logging.Logger:
    """Get the main application logger."""
    global _main_logger
    if _main_logger is None:
        _main_logger, _ = setup_logging()
    return _main_logger


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger."""
    global _performance_logger
    if _performance_logger is None:
        _, _performance_logger = setup_logging()
    return _performance_logger


def get_security_logger() -> SecurityLogger:
    """Get the security logger."""
    global _security_logger
    if _security_logger is None:
        main_logger = get_main_logger()
        _security_logger = SecurityLogger(main_logger)
    return _security_logger

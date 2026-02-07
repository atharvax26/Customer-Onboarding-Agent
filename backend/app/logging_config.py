"""
Logging configuration for Customer Onboarding Agent
Provides structured logging with different levels and formatters
"""

import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'component'):
            log_entry["component"] = record.component
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
        
        return json.dumps(log_entry)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to log record"""
        # Add process ID and thread ID
        record.process_id = os.getpid()
        record.thread_id = record.thread
        
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/app.log",
    enable_json_logging: bool = False,
    enable_console_logging: bool = True
) -> None:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_json_logging: Whether to use JSON formatting
        enable_console_logging: Whether to log to console
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define formatters
    formatters = {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "()": JSONFormatter
        }
    }
    
    # Define handlers
    handlers = {}
    
    if enable_console_logging:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "json" if enable_json_logging else "standard",
            "stream": sys.stdout,
            "filters": ["context"]
        }
    
    handlers["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "level": log_level,
        "formatter": "json" if enable_json_logging else "detailed",
        "filename": log_file,
        "maxBytes": 10485760,  # 10MB
        "backupCount": 5,
        "filters": ["context"]
    }
    
    # Error-specific handler
    handlers["error_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "level": "ERROR",
        "formatter": "json" if enable_json_logging else "detailed",
        "filename": str(log_path.parent / "error.log"),
        "maxBytes": 10485760,  # 10MB
        "backupCount": 5,
        "filters": ["context"]
    }
    
    # Define filters
    filters = {
        "context": {
            "()": ContextFilter
        }
    }
    
    # Define loggers
    loggers = {
        "": {  # Root logger
            "level": log_level,
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "app": {
            "level": log_level,
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"] if enable_console_logging else ["file"],
            "propagate": False
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "error_file"] if enable_console_logging else ["file", "error_file"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["file"],
            "propagate": False
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False
        }
    }
    
    # Configure logging
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "filters": filters,
        "handlers": handlers,
        "loggers": loggers
    }
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with context support
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context information"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any] = None):
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message with context"""
        # Add extra context to the log record
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        kwargs['extra'].update(self.extra)
        return msg, kwargs
    
    def with_context(self, **context) -> 'LoggerAdapter':
        """Create new adapter with additional context"""
        new_extra = self.extra.copy()
        new_extra.update(context)
        return LoggerAdapter(self.logger, new_extra)


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    Get logger with context information
    
    Args:
        name: Logger name
        **context: Context information to include in logs
        
    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)


# Performance monitoring decorator
def log_performance(operation: str):
    """Decorator to log operation performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger(f"app.performance.{func.__module__}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Operation completed: {operation}",
                    extra={
                        "operation": operation,
                        "duration": duration,
                        "function": func.__name__,
                        "success": True
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation failed: {operation}",
                    extra={
                        "operation": operation,
                        "duration": duration,
                        "function": func.__name__,
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


# Async performance monitoring decorator
def log_async_performance(operation: str):
    """Decorator to log async operation performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            logger = get_logger(f"app.performance.{func.__module__}")
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Async operation completed: {operation}",
                    extra={
                        "operation": operation,
                        "duration": duration,
                        "function": func.__name__,
                        "success": True
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Async operation failed: {operation}",
                    extra={
                        "operation": operation,
                        "duration": duration,
                        "function": func.__name__,
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator
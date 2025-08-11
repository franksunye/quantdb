"""
Enhanced logging module for QuantDB.

This module provides a unified logging interface with advanced features:
- Configurable log levels and formats
- Log rotation
- Context-aware logging
- Performance metrics
- Component-specific logging
"""
import logging
import os
import time
import json
import uuid
import functools
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List, Union
from logging.handlers import RotatingFileHandler

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
DETAILED_LOG_FORMAT = '%(asctime)s - %(name)s - [%(levelname)s] - [%(context_id)s] - %(message)s'

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Global context storage
_log_context = {}

class EnhancedLogger:
    """
    Enhanced logger with advanced features for QuantDB.
    """
    
    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: Union[str, int] = logging.INFO,
        format_string: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True,
        detailed: bool = False
    ):
        """
        Initialize the enhanced logger.
        
        Args:
            name: Logger name
            log_file: Path to log file (defaults to logs/[name].log)
            level: Logging level (string or int)
            format_string: Log format string
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
            console_output: Whether to output logs to console
            detailed: Whether to use detailed logging format
        """
        self.name = name
        self.detailed = detailed
        
        # Convert string level to int if needed
        if isinstance(level, str):
            self.level = LOG_LEVELS.get(level.upper(), logging.INFO)
        else:
            self.level = level
        
        # Set default log file if not provided
        if log_file is None:
            log_file = os.path.join(LOG_DIR, f"{name}.log")
        self.log_file = log_file
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Clear existing handlers to avoid duplicates
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Set format
        if format_string is None:
            self.format_string = DETAILED_LOG_FORMAT if detailed else DEFAULT_LOG_FORMAT
        else:
            self.format_string = format_string
        
        # Create formatter
        self.formatter = logging.Formatter(self.format_string)
        
        # Add file handler with rotation and UTF-8 encoding
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.level)
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)
        
        # Initialize context
        self.context_id = None
        self.start_time = None
        self.metrics = {}
    
    def start_context(self, context_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new logging context.
        
        Args:
            context_id: Optional context ID (generates a new one if not provided)
            metadata: Optional metadata to associate with the context
            
        Returns:
            The context ID
        """
        # Generate context ID if not provided
        if context_id is None:
            context_id = str(uuid.uuid4())
        
        self.context_id = context_id
        self.start_time = time.time()
        self.metrics = {}
        
        # Store context
        _log_context[context_id] = {
            'start_time': self.start_time,
            'metadata': metadata or {},
            'metrics': {}
        }
        
        # Log context start
        self._log('info', f"CONTEXT START: {context_id}")
        if metadata:
            self._log('debug', f"CONTEXT METADATA: {json.dumps(metadata)}")
        
        return context_id
    
    def end_context(self) -> float:
        """
        End the current context and log summary.
        
        Returns:
            Total duration in seconds
        """
        if not self.context_id:
            self._log('warning', "Attempted to end context but no context is active")
            return 0.0
        
        # Calculate duration
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Log context end with summary
        self._log('info', f"CONTEXT END: {self.context_id} - Duration: {duration:.4f}s")
        
        # Log metrics if any
        if self.metrics:
            metrics_str = json.dumps(self.metrics)
            self._log('info', f"CONTEXT METRICS: {metrics_str}")
        
        # Clear context
        if self.context_id in _log_context:
            del _log_context[self.context_id]
        
        self.context_id = None
        return duration
    
    def add_metric(self, name: str, value: Any):
        """
        Add a metric to the current context.
        
        Args:
            name: Metric name
            value: Metric value
        """
        if not self.context_id:
            self._log('warning', f"Attempted to add metric '{name}' but no context is active")
            return
        
        self.metrics[name] = value
        
        # Add to global context
        if self.context_id in _log_context:
            _log_context[self.context_id]['metrics'][name] = value
        
        # Log metric
        self._log('debug', f"METRIC: {name} = {value}")
    
    def _log(self, level: str, message: str):
        """
        Internal method to log messages with context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
        """
        # Add context ID to log record
        extra = {'context_id': self.context_id or 'NO_CONTEXT'}
        
        # Call appropriate logger method
        if level == 'debug':
            self.logger.debug(message, extra=extra)
        elif level == 'info':
            self.logger.info(message, extra=extra)
        elif level == 'warning':
            self.logger.warning(message, extra=extra)
        elif level == 'error':
            self.logger.error(message, extra=extra)
        elif level == 'critical':
            self.logger.critical(message, extra=extra)
    
    def debug(self, message: str):
        """Log a debug message"""
        self._log('debug', message)
    
    def info(self, message: str):
        """Log an info message"""
        self._log('info', message)
    
    def warning(self, message: str):
        """Log a warning message"""
        self._log('warning', message)
    
    def error(self, message: str, exc_info: Optional[Exception] = None):
        """
        Log an error message, optionally with exception info.
        
        Args:
            message: Error message
            exc_info: Optional exception instance
        """
        if exc_info:
            tb = traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
            self._log('error', f"{message}\n{''.join(tb)}")
        else:
            self._log('error', message)
    
    def critical(self, message: str, exc_info: Optional[Exception] = None):
        """
        Log a critical message, optionally with exception info.
        
        Args:
            message: Critical message
            exc_info: Optional exception instance
        """
        if exc_info:
            tb = traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
            self._log('critical', f"{message}\n{''.join(tb)}")
        else:
            self._log('critical', message)
    
    def log_data(self, name: str, data: Any, level: str = 'debug'):
        """
        Log data with a name.
        
        Args:
            name: Data name
            data: Data to log
            level: Log level
        """
        try:
            data_str = json.dumps(data) if not isinstance(data, str) else data
            self._log(level, f"DATA [{name}]: {data_str}")
        except (TypeError, ValueError):
            self._log(level, f"DATA [{name}]: {str(data)} (not JSON serializable)")

def log_function(logger=None, level: str = 'info'):
    """
    Decorator to log function calls with timing information.
    
    Args:
        logger: Optional EnhancedLogger instance (creates a new one if not provided)
        level: Log level for function call logs
        
    Returns:
        Decorated function
    """
    def decorator(func):
        # Create logger if not provided
        nonlocal logger
        if logger is None:
            logger = setup_enhanced_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start context
            context_id = logger.start_context()
            
            # Log function call
            args_str = ", ".join([str(arg) for arg in args])
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            params = f"{args_str}{', ' if args_str and kwargs_str else ''}{kwargs_str}"
            logger._log(level, f"FUNCTION START: {func.__name__}({params})")
            
            start_time = time.time()
            try:
                # Call function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Log success
                logger._log(level, f"FUNCTION END: {func.__name__} - Success - Duration: {duration:.4f}s")
                logger.add_metric(f"{func.__name__}_duration", duration)
                
                return result
            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time
                
                # Log error
                logger.error(f"FUNCTION ERROR: {func.__name__} - {type(e).__name__}: {str(e)}", exc_info=e)
                logger.add_metric(f"{func.__name__}_duration", duration)
                logger.add_metric(f"{func.__name__}_error", str(e))
                
                raise
            finally:
                # End context
                logger.end_context()
        
        return wrapper
    return decorator

def setup_enhanced_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Union[str, int] = logging.INFO,
    format_string: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_output: bool = True,
    detailed: bool = False
) -> EnhancedLogger:
    """
    Set up and configure an enhanced logger.
    
    Args:
        name: Logger name
        log_file: Path to log file (defaults to logs/[name].log)
        level: Logging level (string or int)
        format_string: Log format string
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output logs to console
        detailed: Whether to use detailed logging format
        
    Returns:
        Configured EnhancedLogger instance
    """
    return EnhancedLogger(
        name=name,
        log_file=log_file,
        level=level,
        format_string=format_string,
        max_bytes=max_bytes,
        backup_count=backup_count,
        console_output=console_output,
        detailed=detailed
    )

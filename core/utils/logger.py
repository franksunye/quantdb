"""
Core Logging Module

This module provides unified logging functionality for the QuantDB core layer.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import LOG_LEVEL, LOG_FILE


class QuantDBLogger:
    """Unified logger for QuantDB core."""

    def __init__(self, name: str = "quantdb", log_file: Optional[str] = None):
        """
        Initialize the logger.

        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        if log_file or LOG_FILE:
            file_path = log_file or LOG_FILE
            # Create log directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)


# Create default logger instance
logger = QuantDBLogger()


def get_logger(name: str = "quantdb") -> QuantDBLogger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name

    Returns:
        QuantDBLogger instance
    """
    return QuantDBLogger(name)


# Export logger methods for convenience
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical


# Compatibility aliases for integration tests
class EnhancedLogger(QuantDBLogger):
    """Compatibility alias for EnhancedLogger."""

    def __init__(
        self,
        name: str = "quantdb",
        log_file: Optional[str] = None,
        level: str = "INFO",
        console_output: bool = True,
        detailed: bool = False,
    ):
        super().__init__(name, log_file)
        self.context_id = None
        self.start_time = None
        self.metrics = {}

    def start_context(self, metadata: Optional[dict] = None) -> str:
        """Start a logging context (compatibility method)."""
        import uuid
        import time

        self.context_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.info(f"CONTEXT START: {self.context_id}")
        return self.context_id

    def end_context(self) -> float:
        """End the logging context (compatibility method)."""
        import time

        if self.start_time:
            duration = time.time() - self.start_time
            self.info(f"CONTEXT END: {self.context_id}")
            if self.metrics:
                import json

                self.info(f"CONTEXT METRICS: {json.dumps(self.metrics)}")
            return duration
        return 0.0

    def add_metric(self, name: str, value):
        """Add a metric (compatibility method)."""
        self.metrics[name] = value
        self.debug(f"METRIC: {name} = {value}")

    def log_data(self, name: str, data, level: str = "info"):
        """Log data (compatibility method)."""
        import json

        try:
            data_str = json.dumps(data) if not isinstance(data, str) else data
            getattr(self, level)(f"DATA [{name}]: {data_str}")
        except (TypeError, ValueError):
            getattr(self, level)(f"DATA [{name}]: {str(data)} (not JSON serializable)")


def setup_enhanced_logger(name: str, **kwargs) -> EnhancedLogger:
    """Setup enhanced logger (compatibility function)."""
    return EnhancedLogger(name, **kwargs)


def log_function(logger=None, level: str = "info"):
    """Log function decorator (compatibility function)."""
    import functools
    import time

    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = EnhancedLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context_id = logger.start_context()
            logger.info(f"FUNCTION START: {func.__name__}")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"FUNCTION END: {func.__name__} - Success")
                logger.add_metric(f"{func.__name__}_duration", duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"FUNCTION ERROR: {func.__name__} - {type(e).__name__}: {str(e)}")
                logger.add_metric(f"{func.__name__}_duration", duration)
                raise
            finally:
                logger.end_context()

        return wrapper

    return decorator

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
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
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

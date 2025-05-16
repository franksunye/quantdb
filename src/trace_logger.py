"""
Enhanced logging module with tracing capabilities for detailed flow tracking.

This module extends the basic logger with:
- Trace ID generation for tracking requests through the system
- Timing information for performance measurement
- Consistent formatting for flow visualization
- Debug mode for detailed logging
"""
import logging
import os
import time
import uuid
import functools
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# Global trace context dictionary
_trace_context = {}

class TraceLogger:
    """
    Enhanced logger with tracing capabilities for detailed flow tracking.
    """

    def __init__(self, name: str, log_file: Optional[str] = None, level=logging.INFO,
                 debug_mode: bool = False):
        """
        Initialize the trace logger.

        Args:
            name: Logger name
            log_file: Path to log file (defaults to logs/[name].log)
            level: Logging level
            debug_mode: Whether to enable debug mode for detailed logging
        """
        self.name = name
        self.debug_mode = debug_mode

        # Set default log file if not provided
        if log_file is None:
            log_file = os.path.join(LOG_DIR, f"{name}.log")

        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug_mode else level)

        # Clear existing handlers to avoid duplicates
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug_mode else level)

        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG if debug_mode else level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(trace_id)s] - %(levelname)s - %(message)s'
        )

        # Set formatter for handlers
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        # Initialize trace ID
        self.trace_id = None
        self.start_time = None
        self.step_times = {}

    def start_trace(self, trace_id: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new trace with optional context information.

        Args:
            trace_id: Optional trace ID (generates a new one if not provided)
            context: Optional context information to store with the trace

        Returns:
            The trace ID
        """
        # Generate trace ID if not provided
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        self.trace_id = trace_id
        self.start_time = time.time()
        self.step_times = {}

        # Store context information
        global _trace_context
        _trace_context[trace_id] = {
            'start_time': self.start_time,
            'context': context or {},
            'steps': []
        }

        # Log trace start
        self._log('info', f"TRACE START: {trace_id}")
        if context:
            self._log('debug', f"TRACE CONTEXT: {context}")

        return trace_id

    def end_trace(self) -> float:
        """
        End the current trace and log summary information.

        Returns:
            Total trace duration in seconds
        """
        if not self.trace_id:
            self._log('warning', "Attempted to end trace but no trace is active")
            return 0.0

        # Calculate total duration
        end_time = time.time()
        duration = end_time - self.start_time

        # Log trace end with summary
        self._log('info', f"TRACE END: {self.trace_id} - Total duration: {duration:.4f}s")

        # Log step durations if in debug mode
        if self.debug_mode and self.step_times:
            steps_info = "\n  ".join([f"{step}: {duration:.4f}s" for step, duration in self.step_times.items()])
            self._log('debug', f"TRACE STEPS:\n  {steps_info}")

        # Clear trace context
        if self.trace_id in _trace_context:
            del _trace_context[self.trace_id]

        self.trace_id = None
        return duration

    def step(self, name: str) -> float:
        """
        Mark a step in the trace and record its timing.

        Args:
            name: Step name

        Returns:
            Time elapsed since trace start in seconds
        """
        if not self.trace_id:
            self._log('warning', f"Step '{name}' recorded but no trace is active")
            return 0.0

        current_time = time.time()
        elapsed = current_time - self.start_time

        # Store step timing
        self.step_times[name] = elapsed

        # Add to trace context
        if self.trace_id in _trace_context:
            _trace_context[self.trace_id]['steps'].append({
                'name': name,
                'time': current_time,
                'elapsed': elapsed
            })

        # Log step information
        self._log('info', f"STEP: {name} - Elapsed: {elapsed:.4f}s")

        return elapsed

    def transition(self, from_component: str, to_component: str, details: Optional[str] = None):
        """
        Log a transition between components.

        Args:
            from_component: Source component
            to_component: Destination component
            details: Optional details about the transition
        """
        message = f"TRANSITION: {from_component} -> {to_component}"
        if details:
            message += f" - {details}"

        self._log('info', message)

    def _log(self, level: str, message: str):
        """
        Internal method to log messages with trace context.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
        """
        # Add trace ID to log record, use 'NO_TRACE' if no trace is active
        # The expression self.trace_id or 'NO_TRACE' will return 'NO_TRACE' if self.trace_id is None,
        # but it will also return 'NO_TRACE' if self.trace_id is an empty string or False,
        # which might not be the intended behavior.
        extra = {'trace_id': self.trace_id if self.trace_id is not None else 'NO_TRACE'}

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

    def error(self, message: str):
        """Log an error message"""
        self._log('error', message)

    def critical(self, message: str):
        """Log a critical message"""
        self._log('critical', message)

    def data(self, name: str, data: Any):
        """
        Log data with a name for debugging purposes.
        Only logs in debug mode.

        Args:
            name: Data name
            data: Data to log
        """
        if self.debug_mode:
            self._log('debug', f"DATA [{name}]: {data}")


def trace_function(logger=None):
    """
    Decorator to trace function execution with timing information.

    Args:
        logger: Optional TraceLogger instance (creates a new one if not provided)

    Returns:
        Decorated function
    """
    def decorator(func):
        # Create logger if not provided
        nonlocal logger
        if logger is None:
            logger = TraceLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start trace
            trace_id = logger.start_trace()

            # Log function call
            args_str = ", ".join([str(arg) for arg in args])
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            params = f"{args_str}{', ' if args_str and kwargs_str else ''}{kwargs_str}"
            logger.info(f"FUNCTION START: {func.__name__}({params})")

            try:
                # Call function
                result = func(*args, **kwargs)

                # Log success
                logger.info(f"FUNCTION END: {func.__name__} - Success")

                return result
            except Exception as e:
                # Log error
                logger.error(f"FUNCTION ERROR: {func.__name__} - {type(e).__name__}: {str(e)}")
                raise
            finally:
                # End trace
                logger.end_trace()

        return wrapper
    return decorator


def setup_trace_logger(name: str, log_file: Optional[str] = None,
                      level=logging.INFO, debug_mode: bool = False) -> TraceLogger:
    """
    Set up and configure a trace logger.

    Args:
        name: Logger name
        log_file: Path to log file (defaults to logs/[name].log)
        level: Logging level
        debug_mode: Whether to enable debug mode for detailed logging

    Returns:
        Configured TraceLogger instance
    """
    return TraceLogger(name, log_file, level, debug_mode)

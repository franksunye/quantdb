import logging
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

def setup_logger(log_name="quantdb", log_file=None, level=logging.INFO):
    """
    Set up and configure a logger

    Args:
        log_name: Name of the logger
        log_file: Path to the log file. If None, defaults to logs/[log_name].log
        level: Logging level

    Returns:
        A configured logger instance
    """
    # Create logger
    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Set default log file if not provided
    if log_file is None:
        log_file = os.path.join(LOG_DIR, f"{log_name}.log")

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set formatter for handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Initialize default logger
logger = setup_logger(log_file=os.path.join(LOG_DIR, "quantdb.log"))

# 示例：使用日志记录器
def example_function():
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.error("This is an error message")

if __name__ == "__main__":
    example_function()

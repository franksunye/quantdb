"""
QDB Exception Class Definitions

Provides user-friendly exception information and error handling
"""


class QDBError(Exception):
    """QDB base exception class"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class CacheError(QDBError):
    """Cache-related exceptions"""

    def __init__(self, message: str):
        super().__init__(message, "CACHE_ERROR")


class DataError(QDBError):
    """Data acquisition related exceptions"""

    def __init__(self, message: str):
        super().__init__(message, "DATA_ERROR")


class NetworkError(QDBError):
    """Network request related exceptions"""

    def __init__(self, message: str):
        super().__init__(message, "NETWORK_ERROR")


class ConfigError(QDBError):
    """Configuration related exceptions"""

    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(QDBError):
    """Data validation related exceptions"""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


# Exception handling decorator
def handle_qdb_errors(func):
    """
    QDB exception handling decorator

    Automatically catch and convert common exceptions to QDB exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QDBError:
            # QDB exceptions are raised directly
            raise
        except ImportError as e:
            raise ConfigError(f"Missing required dependency: {str(e)}")
        except FileNotFoundError as e:
            raise CacheError(f"Cache file not found: {str(e)}")
        except PermissionError as e:
            raise CacheError(f"Insufficient cache directory permissions: {str(e)}")
        except ConnectionError as e:
            raise NetworkError(f"Network connection failed: {str(e)}")
        except ValueError as e:
            raise ValidationError(f"Data validation failed: {str(e)}")
        except Exception as e:
            raise QDBError(f"Unknown error: {str(e)}")

    return wrapper


# Error code definitions
ERROR_CODES = {
    "CACHE_ERROR": "Cache operation failed",
    "DATA_ERROR": "Data acquisition failed",
    "NETWORK_ERROR": "Network request failed",
    "CONFIG_ERROR": "Configuration error",
    "VALIDATION_ERROR": "Data validation failed"
}


def get_error_message(error_code: str) -> str:
    """
    Get error description based on error code

    Args:
        error_code: Error code

    Returns:
        Error description message
    """
    return ERROR_CODES.get(error_code, "Unknown error")


# User-friendly error prompts
def format_user_error(error: Exception) -> str:
    """
    Format user-friendly error messages

    Args:
        error: Exception object

    Returns:
        Formatted error message
    """
    if isinstance(error, QDBError):
        return f"❌ QDB Error: {error.message}"
    elif isinstance(error, ImportError):
        return f"❌ Dependency Error: Please install required dependencies\n   Solution: pip install quantdb[full]"
    elif isinstance(error, FileNotFoundError):
        return f"❌ File Error: {str(error)}\n   Solution: Check file path or reinitialize cache"
    elif isinstance(error, PermissionError):
        return f"❌ Permission Error: {str(error)}\n   Solution: Check directory permissions or change cache directory"
    elif isinstance(error, ConnectionError):
        return f"❌ Network Error: {str(error)}\n   Solution: Check network connection or retry later"
    else:
        return f"❌ Unknown Error: {str(error)}\n   Suggestion: Please check input parameters or contact technical support"

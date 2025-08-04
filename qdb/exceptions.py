"""
QDB异常类定义

提供用户友好的异常信息和错误处理
"""


class QDBError(Exception):
    """QDB基础异常类"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class CacheError(QDBError):
    """缓存相关异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "CACHE_ERROR")


class DataError(QDBError):
    """数据获取相关异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "DATA_ERROR")


class NetworkError(QDBError):
    """网络请求相关异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "NETWORK_ERROR")


class ConfigError(QDBError):
    """配置相关异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(QDBError):
    """数据验证相关异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


# 异常处理装饰器
def handle_qdb_errors(func):
    """
    QDB异常处理装饰器
    
    自动捕获和转换常见异常为QDB异常
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QDBError:
            # QDB异常直接抛出
            raise
        except ImportError as e:
            raise ConfigError(f"缺少必要的依赖包: {str(e)}")
        except FileNotFoundError as e:
            raise CacheError(f"缓存文件未找到: {str(e)}")
        except PermissionError as e:
            raise CacheError(f"缓存目录权限不足: {str(e)}")
        except ConnectionError as e:
            raise NetworkError(f"网络连接失败: {str(e)}")
        except ValueError as e:
            raise ValidationError(f"数据验证失败: {str(e)}")
        except Exception as e:
            raise QDBError(f"未知错误: {str(e)}")
    
    return wrapper


# 错误码定义
ERROR_CODES = {
    "CACHE_ERROR": "缓存操作失败",
    "DATA_ERROR": "数据获取失败", 
    "NETWORK_ERROR": "网络请求失败",
    "CONFIG_ERROR": "配置错误",
    "VALIDATION_ERROR": "数据验证失败"
}


def get_error_message(error_code: str) -> str:
    """
    根据错误码获取错误描述
    
    Args:
        error_code: 错误码
        
    Returns:
        错误描述信息
    """
    return ERROR_CODES.get(error_code, "未知错误")


# 用户友好的错误提示
def format_user_error(error: Exception) -> str:
    """
    格式化用户友好的错误信息
    
    Args:
        error: 异常对象
        
    Returns:
        格式化的错误信息
    """
    if isinstance(error, QDBError):
        return f"❌ QDB错误: {error.message}"
    elif isinstance(error, ImportError):
        return f"❌ 依赖错误: 请安装必要的依赖包\n   解决方案: pip install qdb[full]"
    elif isinstance(error, FileNotFoundError):
        return f"❌ 文件错误: {str(error)}\n   解决方案: 检查文件路径或重新初始化缓存"
    elif isinstance(error, PermissionError):
        return f"❌ 权限错误: {str(error)}\n   解决方案: 检查目录权限或更改缓存目录"
    elif isinstance(error, ConnectionError):
        return f"❌ 网络错误: {str(error)}\n   解决方案: 检查网络连接或稍后重试"
    else:
        return f"❌ 未知错误: {str(error)}\n   建议: 请检查输入参数或联系技术支持"

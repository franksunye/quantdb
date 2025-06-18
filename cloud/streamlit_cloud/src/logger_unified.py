"""
统一的日志接口 - 简化版本

这个模块提供统一的日志接口，解决项目中日志使用不一致的问题。
基于现有的 enhanced_logger.py，提供简单统一的使用方式。
"""

import os
from src.enhanced_logger import setup_enhanced_logger

# 简单的配置获取，避免依赖复杂的config模块
def _get_log_level():
    """获取日志级别"""
    return os.getenv('LOG_LEVEL', 'INFO')

def _is_debug():
    """检查是否为调试模式"""
    return os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

def get_logger(name: str):
    """
    获取统一配置的日志记录器

    Args:
        name: 日志记录器名称，通常使用 __name__

    Returns:
        配置好的 EnhancedLogger 实例
    """
    return setup_enhanced_logger(
        name=name,
        level="DEBUG" if _is_debug() else _get_log_level(),
        detailed=True,
        console_output=True
    )

# 为了兼容性，提供旧的接口
def setup_logger(name: str):
    """兼容旧的 setup_logger 接口"""
    return get_logger(name)

# 默认日志记录器
logger = get_logger('quantdb')

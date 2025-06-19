"""
QuantDB Cloud Edition 配置管理

管理云端版本的配置参数和常量。
"""

import os
from typing import Dict, Any

class Config:
    """云端版本配置类"""
    
    # 应用配置
    APP_TITLE = "QuantDB Cloud - 量化数据平台"
    APP_VERSION = "v1.1.0-cloud"
    APP_DESCRIPTION = "高性能股票数据缓存服务 - 云端版"
    
    # 页面配置
    PAGE_ICON = "📊"
    LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"
    
    # 数据配置
    DEFAULT_DAYS = 30  # 默认查询天数
    MAX_DAYS = 365     # 最大查询天数
    MIN_DAYS = 1       # 最小查询天数
    
    # 图表配置
    CHART_HEIGHT = 400
    CHART_WIDTH = None  # 使用容器宽度
    
    # 颜色配置
    COLORS = {
        "primary": "#1f77b4",      # 深蓝色 - 主色调
        "success": "#2ca02c",      # 绿色 - 上涨/正面
        "danger": "#d62728",       # 红色 - 下跌/警告
        "warning": "#ff7f0e",      # 橙色 - 警告
        "info": "#17a2b8",         # 浅蓝色 - 信息
        "light": "#f8f9fa",        # 浅灰色 - 背景
        "dark": "#343a40"          # 深灰色 - 文字
    }
    
    # 测试数据
    TEST_SYMBOLS = ["600000", "000001", "600519", "000002", "600036"]
    TEST_SYMBOL_NAMES = {
        "600000": "浦发银行",
        "000001": "平安银行", 
        "600519": "贵州茅台",
        "000002": "万科A",
        "600036": "招商银行"
    }
    
    # 缓存配置
    CACHE_TTL = 300  # 前端缓存TTL (秒)
    
    # 错误消息
    ERROR_MESSAGES = {
        "service_connection": "无法连接到数据服务，请检查服务是否正常",
        "invalid_symbol": "股票代码格式错误，请输入有效代码 (A股: 600000, 港股: 02171)",
        "invalid_date": "日期格式错误或日期范围无效",
        "no_data": "未找到指定时间范围内的数据",
        "server_error": "服务器内部错误，请稍后重试",
        "timeout": "请求超时，请检查网络连接",
        "database_error": "数据库连接错误，请联系技术支持"
    }
    
    # 成功消息
    SUCCESS_MESSAGES = {
        "data_loaded": "数据加载成功",
        "cache_hit": "数据来自缓存，响应速度极快",
        "service_healthy": "数据服务运行正常",
        "database_connected": "数据库连接正常"
    }
    
    @classmethod
    def get_color(cls, color_name: str) -> str:
        """获取颜色值"""
        return cls.COLORS.get(color_name, cls.COLORS["primary"])
    
    @classmethod
    def get_test_symbol_name(cls, symbol: str) -> str:
        """获取测试股票的中文名称"""
        return cls.TEST_SYMBOL_NAMES.get(symbol, f"股票 {symbol}")
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """验证股票代码格式 - 支持A股和港股"""
        if not symbol:
            return False

        # 港股: 5位数字，通常以0开头 (02171, 00700)
        if symbol.isdigit() and len(symbol) == 5 and symbol.startswith('0'):
            return True

        # 移除可能的前缀和后缀 (仅对A股)
        clean_symbol = symbol.upper().replace("SH", "").replace("SZ", "").replace(".SH", "").replace(".SZ", "")

        # A股: 6位数字 (000001, 600000)
        if clean_symbol.isdigit() and len(clean_symbol) == 6:
            return True

        return False
    
    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        """标准化股票代码 - 支持A股和港股"""
        if not symbol:
            return ""

        # 检测是否为港股 (5位数字)
        if symbol.isdigit() and len(symbol) == 5:
            return symbol  # 港股代码保持原样

        # A股处理: 移除前缀和后缀，转换为大写
        clean_symbol = symbol.upper().replace("SH", "").replace("SZ", "").replace(".SH", "").replace(".SZ", "").rstrip(".")

        # 如果长度不足6位，前面补0 (仅对A股)
        if clean_symbol.isdigit():
            return clean_symbol.zfill(6)

        return clean_symbol

# 创建全局配置实例
config = Config()

# 导出常用配置
COLORS = config.COLORS
TEST_SYMBOLS = config.TEST_SYMBOLS
ERROR_MESSAGES = config.ERROR_MESSAGES
SUCCESS_MESSAGES = config.SUCCESS_MESSAGES

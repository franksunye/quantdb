"""
QuantDB Frontend Configuration Management

Manages configuration parameters and constants for the frontend application.
"""

import os
from typing import Dict, Any


class Config:
    """Frontend configuration class"""

    # API Configuration
    API_BASE_URL = os.getenv("QUANTDB_API_URL", "http://localhost:8000")
    API_PREFIX = "/api/v1"
    API_TIMEOUT = int(
        os.getenv("API_TIMEOUT", "300")
    )  # seconds - increased to 5 minutes for initial data fetch

    # Application Configuration
    APP_TITLE = "QuantDB - Quantitative Data Platform"
    APP_VERSION = "v1.0.0-mvp"
    APP_DESCRIPTION = "High-Performance Stock Data Caching Service Frontend"

    # Page Configuration
    PAGE_ICON = "📊"
    LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"

    # Data Configuration
    DEFAULT_DAYS = 30  # default query days
    MAX_DAYS = 365  # maximum query days
    MIN_DAYS = 1  # minimum query days

    # Chart Configuration
    CHART_HEIGHT = 400
    CHART_WIDTH = None  # use container width

    # 颜色配置
    COLORS = {
        "primary": "#1f77b4",  # 深蓝色 - 主色调
        "success": "#2ca02c",  # 绿色 - 上涨/正面
        "danger": "#d62728",  # 红色 - 下跌/警告
        "warning": "#ff7f0e",  # 橙色 - 警告
        "info": "#17a2b8",  # 浅蓝色 - 信息
        "light": "#f8f9fa",  # 浅灰色 - 背景
        "dark": "#343a40",  # 深灰色 - 文字
    }

    # 测试数据
    TEST_SYMBOLS = ["600000", "000001", "600519", "000002", "600036"]
    TEST_SYMBOL_NAMES = {
        "600000": "浦发银行",
        "000001": "平安银行",
        "600519": "贵州茅台",
        "000002": "万科A",
        "600036": "招商银行",
    }

    # Cache Configuration
    CACHE_TTL = 300  # frontend cache TTL (seconds)

    # Error Messages
    ERROR_MESSAGES = {
        "api_connection": "Unable to connect to backend API service, please check if the service is running",
        "invalid_symbol": "Invalid stock symbol format, please enter a valid code (A-Share: 600000, HK Stock: 02171)",
        "invalid_date": "Invalid date format or date range",
        "no_data": "No data found for the specified time range",
        "server_error": "Internal server error, please try again later",
        "timeout": "Request timeout, please check your network connection",
    }

    # Success Messages
    SUCCESS_MESSAGES = {
        "data_loaded": "Data loaded successfully",
        "cache_hit": "Data from cache, extremely fast response",
        "api_healthy": "API service is running normally",
    }

    @classmethod
    def get_api_url(cls, endpoint: str = "") -> str:
        """Get complete API URL"""
        return f"{cls.API_BASE_URL}{cls.API_PREFIX}{endpoint}"

    @classmethod
    def get_color(cls, color_name: str) -> str:
        """Get color value"""
        return cls.COLORS.get(color_name, cls.COLORS["primary"])

    @classmethod
    def get_test_symbol_name(cls, symbol: str) -> str:
        """获取测试股票的中文名称"""
        return cls.TEST_SYMBOL_NAMES.get(symbol, f"股票 {symbol}")

    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """验证股票代码格式 - 支持A股和港股"""
        if not symbol or not symbol.isdigit():
            return False

        # 移除可能的前缀和后缀 (仅对A股)
        clean_symbol = (
            symbol.upper().replace("SH", "").replace("SZ", "").replace(".SH", "").replace(".SZ", "")
        )

        # A股: 6位数字 (000001, 600000)
        if clean_symbol.isdigit() and len(clean_symbol) == 6:
            return True

        # 港股: 5位数字 (02171, 00700)
        if symbol.isdigit() and len(symbol) == 5:
            return True

        return False

    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        """Normalize stock symbol - supports A-Share and HK stocks"""
        if not symbol:
            return ""

        # Detect if it's HK stock (5 digits)
        if symbol.isdigit() and len(symbol) == 5:
            return symbol  # Keep HK stock code as is

        # A-Share processing: remove prefix and suffix, convert to uppercase
        clean_symbol = (
            symbol.upper()
            .replace("SH", "")
            .replace("SZ", "")
            .replace(".SH", "")
            .replace(".SZ", "")
            .rstrip(".")
        )

        # If length is less than 6 digits, pad with zeros (A-Share only)
        if clean_symbol.isdigit():
            return clean_symbol.zfill(6)

        return clean_symbol


# Create global configuration instance
config = Config()

# Export common configurations
API_BASE_URL = config.API_BASE_URL
API_PREFIX = config.API_PREFIX
COLORS = config.COLORS
TEST_SYMBOLS = config.TEST_SYMBOLS
ERROR_MESSAGES = config.ERROR_MESSAGES
SUCCESS_MESSAGES = config.SUCCESS_MESSAGES

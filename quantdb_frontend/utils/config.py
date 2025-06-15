"""
QuantDB Frontend 配置管理

管理前端应用的配置参数和常量。
"""

import os
from typing import Dict, Any

class Config:
    """前端配置类"""
    
    # API配置
    API_BASE_URL = os.getenv("QUANTDB_API_URL", "http://localhost:8000")
    API_PREFIX = "/api/v1"
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "300"))  # 秒 - 增加到5分钟以支持首次数据获取
    
    # 应用配置
    APP_TITLE = "QuantDB - 量化数据平台"
    APP_VERSION = "v1.0.0-mvp"
    APP_DESCRIPTION = "高性能股票数据缓存服务前端"
    
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
        "api_connection": "无法连接到后端API服务，请检查服务是否启动",
        "invalid_symbol": "股票代码格式错误，请输入6位数字代码",
        "invalid_date": "日期格式错误或日期范围无效",
        "no_data": "未找到指定时间范围内的数据",
        "server_error": "服务器内部错误，请稍后重试",
        "timeout": "请求超时，请检查网络连接"
    }
    
    # 成功消息
    SUCCESS_MESSAGES = {
        "data_loaded": "数据加载成功",
        "cache_hit": "数据来自缓存，响应速度极快",
        "api_healthy": "API服务运行正常"
    }
    
    @classmethod
    def get_api_url(cls, endpoint: str = "") -> str:
        """获取完整的API URL"""
        return f"{cls.API_BASE_URL}{cls.API_PREFIX}{endpoint}"
    
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
        """验证股票代码格式"""
        if not symbol:
            return False
        
        # 移除可能的前缀和后缀
        clean_symbol = symbol.upper().replace("SH", "").replace("SZ", "").replace(".SH", "").replace(".SZ", "")
        
        # 检查是否为6位数字
        return clean_symbol.isdigit() and len(clean_symbol) == 6
    
    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        """标准化股票代码"""
        if not symbol:
            return ""

        # 移除前缀和后缀，转换为大写
        clean_symbol = symbol.upper().replace("SH", "").replace("SZ", "").replace(".SH", "").replace(".SZ", "").rstrip(".")

        # 如果长度不足6位，前面补0
        if clean_symbol.isdigit():
            return clean_symbol.zfill(6)

        return clean_symbol

# 创建全局配置实例
config = Config()

# 导出常用配置
API_BASE_URL = config.API_BASE_URL
API_PREFIX = config.API_PREFIX
COLORS = config.COLORS
TEST_SYMBOLS = config.TEST_SYMBOLS
ERROR_MESSAGES = config.ERROR_MESSAGES
SUCCESS_MESSAGES = config.SUCCESS_MESSAGES

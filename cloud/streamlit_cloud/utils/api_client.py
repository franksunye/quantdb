"""
QuantDB API 客户端

封装对QuantDB后端API的调用，提供统一的接口和错误处理。
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from .config import config

# 设置日志
logger = logging.getLogger(__name__)


class QuantDBAPIError(Exception):
    """QuantDB API错误"""

    pass


class QuantDBClient:
    """QuantDB API客户端"""

    def __init__(self, base_url: str = None, timeout: int = None):
        """
        初始化API客户端

        Args:
            base_url: API基础URL
            timeout: 请求超时时间(秒)
        """
        self.base_url = base_url or config.API_BASE_URL
        self.api_prefix = config.API_PREFIX
        self.timeout = timeout or config.API_TIMEOUT
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": f"QuantDB-Frontend/{config.APP_VERSION}",
            }
        )

    def _get_url(self, endpoint: str) -> str:
        """构建完整的API URL"""
        return f"{self.base_url}{self.api_prefix}{endpoint}"

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            API响应数据

        Raises:
            QuantDBAPIError: API调用失败
        """
        url = self._get_url(endpoint)

        try:
            response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)

            # 检查HTTP状态码
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise QuantDBAPIError("数据未找到")
            elif response.status_code == 422:
                raise QuantDBAPIError("请求参数错误")
            elif response.status_code >= 500:
                raise QuantDBAPIError("服务器内部错误")
            else:
                raise QuantDBAPIError(f"API调用失败: HTTP {response.status_code}")

        except requests.exceptions.ConnectionError:
            raise QuantDBAPIError(config.ERROR_MESSAGES["api_connection"])
        except requests.exceptions.Timeout:
            raise QuantDBAPIError(config.ERROR_MESSAGES["timeout"])
        except requests.exceptions.RequestException as e:
            raise QuantDBAPIError(f"网络请求失败: {str(e)}")
        except ValueError as e:
            raise QuantDBAPIError(f"响应数据解析失败: {str(e)}")

    def get_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态

        Returns:
            健康状态信息
        """
        return self._make_request("GET", "/health")

    def get_stock_data(
        self, symbol: str, start_date: str, end_date: str, adjust: str = ""
    ) -> Dict[str, Any]:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ("", "qfq", "hfq")

        Returns:
            股票历史数据
        """
        # 验证股票代码
        if not config.validate_symbol(symbol):
            raise QuantDBAPIError(config.ERROR_MESSAGES["invalid_symbol"])

        # 标准化股票代码
        symbol = config.normalize_symbol(symbol)

        params = {"start_date": start_date, "end_date": end_date}

        if adjust:
            params["adjust"] = adjust

        return self._make_request("GET", f"/historical/stock/{symbol}", params=params)

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取资产信息

        Args:
            symbol: 股票代码

        Returns:
            资产信息
        """
        # 验证股票代码
        if not config.validate_symbol(symbol):
            raise QuantDBAPIError(config.ERROR_MESSAGES["invalid_symbol"])

        # 标准化股票代码
        symbol = config.normalize_symbol(symbol)

        return self._make_request("GET", f"/assets/symbol/{symbol}")

    def get_assets_list(
        self,
        skip: int = 0,
        limit: int = 100,
        symbol: Optional[str] = None,
        name: Optional[str] = None,
        asset_type: Optional[str] = None,
        exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取资产列表

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            symbol: 按股票代码过滤
            name: 按名称过滤
            asset_type: 按资产类型过滤
            exchange: 按交易所过滤

        Returns:
            资产列表
        """
        params = {"skip": skip, "limit": limit}

        if symbol:
            params["symbol"] = symbol
        if name:
            params["name"] = name
        if asset_type:
            params["asset_type"] = asset_type
        if exchange:
            params["exchange"] = exchange

        return self._make_request("GET", "/assets", params=params)

    def get_cache_status(self) -> Dict[str, Any]:
        """
        获取缓存状态

        Returns:
            缓存状态信息
        """
        return self._make_request("GET", "/cache/status")

    def get_version_info(self) -> Dict[str, Any]:
        """
        获取版本信息

        Returns:
            版本信息
        """
        return self._make_request("GET", "/version/latest")


# 创建全局客户端实例
@st.cache_resource
def get_api_client() -> QuantDBClient:
    """获取API客户端实例 (带缓存)"""
    return QuantDBClient()


# 便捷函数
def format_date_for_api(date_obj: date) -> str:
    """将日期对象格式化为API所需的字符串格式"""
    return date_obj.strftime("%Y%m%d")


def parse_api_date(date_str: str) -> datetime:
    """解析API返回的日期字符串"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            raise ValueError(f"无法解析日期格式: {date_str}")


def handle_api_error(func):
    """API错误处理装饰器"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QuantDBAPIError as e:
            st.error(f"API调用失败: {str(e)}")
            return None
        except Exception as e:
            st.error(f"未知错误: {str(e)}")
            logger.exception("API调用发生未知错误")
            return None

    return wrapper


# 测试连接函数
def test_api_connection() -> bool:
    """测试API连接是否正常"""
    try:
        client = get_api_client()
        health = client.get_health()
        return health.get("status") == "ok"
    except:
        return False

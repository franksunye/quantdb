#!/usr/bin/env python3
"""
批量API客户端工具

提供高性能的批量数据获取功能，优化大量股票数据查询的性能。
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from .api_client import QuantDBAPIError, QuantDBClient
from .config import config

logger = logging.getLogger(__name__)


class BatchQuantDBClient:
    """
    批量QuantDB API客户端

    提供高性能的批量数据获取功能：
    - 批量资产信息获取
    - 并发历史数据查询
    - 智能缓存利用
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.API_BASE_URL
        self.api_prefix = config.API_PREFIX
        self.client = QuantDBClient(base_url)

    def get_batch_assets_minimal(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取最小资产信息（仅名称和基本信息）

        这是最快的批量查询方式，适用于显示股票列表。

        Args:
            symbols: 股票代码列表

        Returns:
            字典，键为股票代码，值为资产信息
        """
        try:
            url = f"{self.base_url}{self.api_prefix}/batch/assets/minimal"
            response = requests.post(url, json=symbols, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"批量获取最小资产信息失败: {e}")
            return {}

    def get_batch_assets_full(self, symbols: List[str], use_cache: bool = True) -> Dict[str, Any]:
        """
        批量获取完整资产信息

        Args:
            symbols: 股票代码列表
            use_cache: 是否使用缓存

        Returns:
            批量查询结果
        """
        try:
            url = f"{self.base_url}{self.api_prefix}/batch/assets"
            payload = {"symbols": symbols, "include_financial_data": True, "use_cache": use_cache}
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"批量获取完整资产信息失败: {e}")
            return {
                "success_count": 0,
                "error_count": len(symbols),
                "assets": {},
                "errors": {symbol: str(e) for symbol in symbols},
                "metadata": {},
            }

    def get_batch_stock_data_concurrent(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        max_workers: int = 5,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        并发获取多只股票的历史数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            max_workers: 最大并发数
            progress_callback: 进度回调函数

        Returns:
            批量查询结果
        """
        results = {}
        errors = {}

        def fetch_single_stock(symbol: str) -> tuple:
            """获取单只股票数据"""
            try:
                data = self.client.get_stock_data(symbol, start_date, end_date)
                return symbol, data, None
            except Exception as e:
                return symbol, None, str(e)

        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(fetch_single_stock, symbol): symbol for symbol in symbols
            }

            completed = 0
            total = len(symbols)

            # 处理完成的任务
            for future in as_completed(future_to_symbol):
                symbol, data, error = future.result()

                if error:
                    errors[symbol] = error
                else:
                    results[symbol] = data

                completed += 1

                # 调用进度回调
                if progress_callback:
                    progress_callback(completed, total, symbol)

        return {
            "success_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors,
            "metadata": {
                "total_requested": len(symbols),
                "start_date": start_date,
                "end_date": end_date,
                "max_workers": max_workers,
            },
        }

    def get_watchlist_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """
        获取自选股汇总信息

        优化的自选股查询，结合最小资产信息和简单价格数据。

        Args:
            symbols: 股票代码列表

        Returns:
            自选股汇总信息
        """
        # 首先获取最小资产信息
        assets_info = self.get_batch_assets_minimal(symbols)

        # 然后获取最近价格数据（使用较短的时间范围）
        from datetime import date, timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=5)

        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # 并发获取价格数据
        price_data = self.get_batch_stock_data_concurrent(
            symbols, start_date_str, end_date_str, max_workers=3
        )

        # 合并数据
        summary = {}
        for symbol in symbols:
            asset_info = assets_info.get(symbol, {})
            stock_data = price_data["results"].get(symbol, {})

            # 提取最新价格信息
            latest_price = None
            price_change = None

            if stock_data and "data" in stock_data and stock_data["data"]:
                latest_data = stock_data["data"][-1]
                prev_data = stock_data["data"][-2] if len(stock_data["data"]) > 1 else latest_data

                latest_price = latest_data.get("close")
                if latest_price and prev_data.get("close"):
                    price_change = ((latest_price - prev_data["close"]) / prev_data["close"]) * 100

            summary[symbol] = {
                "name": asset_info.get("name", f"Stock {symbol}"),
                "industry": asset_info.get("industry", "其他"),
                "latest_price": latest_price,
                "price_change_pct": price_change,
                "data_source": asset_info.get("data_source", "unknown"),
                "has_price_data": latest_price is not None,
            }

        return {
            "summary": summary,
            "metadata": {
                "total_symbols": len(symbols),
                "assets_found": len(
                    [s for s in summary.values() if s["name"] != f"Stock {symbol}"]
                ),
                "price_data_found": len([s for s in summary.values() if s["has_price_data"]]),
                "query_date": end_date_str,
            },
        }


def get_batch_client() -> BatchQuantDBClient:
    """获取批量客户端实例"""
    return BatchQuantDBClient()


# Streamlit 集成函数
def st_batch_progress(completed: int, total: int, current_symbol: str):
    """Streamlit进度显示函数"""
    if hasattr(st, "session_state") and "batch_progress" in st.session_state:
        progress_bar = st.session_state.batch_progress["bar"]
        status_text = st.session_state.batch_progress["text"]

        progress = completed / total
        progress_bar.progress(progress)
        status_text.text(f"正在处理 {current_symbol} ({completed}/{total})")


def create_st_batch_progress():
    """创建Streamlit批量进度显示组件"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    if "batch_progress" not in st.session_state:
        st.session_state.batch_progress = {}

    st.session_state.batch_progress["bar"] = progress_bar
    st.session_state.batch_progress["text"] = status_text

    return st_batch_progress

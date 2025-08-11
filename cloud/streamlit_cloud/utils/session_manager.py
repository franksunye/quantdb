"""
会话状态管理器
负责管理Streamlit会话状态和数据缓存
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional


class SessionDataManager:
    """会话数据管理器"""

    @staticmethod
    def init_session():
        """初始化会话状态"""
        defaults = {
            "stock_data_cache": {},
            "asset_info_cache": {},
            "performance_metrics": {
                "total_queries": 0,
                "cache_hits": 0,
                "akshare_calls": 0,
                "avg_response_time": 0,
                "query_history": [],
            },
            "user_preferences": {
                "default_days": 30,
                "chart_theme": "plotly_white",
                "auto_refresh": False,
            },
            "app_start_time": datetime.now(),
            "last_activity": datetime.now(),
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def get_stock_data_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取股票数据"""
        return st.session_state.stock_data_cache.get(cache_key)

    @staticmethod
    def set_stock_data_to_cache(cache_key: str, data: Dict[str, Any]):
        """设置股票数据到缓存"""
        st.session_state.stock_data_cache[cache_key] = data
        st.session_state.last_activity = datetime.now()

    @staticmethod
    def get_asset_info_from_cache(symbol: str) -> Optional[Dict[str, Any]]:
        """从缓存获取资产信息"""
        return st.session_state.asset_info_cache.get(symbol)

    @staticmethod
    def set_asset_info_to_cache(symbol: str, data: Dict[str, Any]):
        """设置资产信息到缓存"""
        st.session_state.asset_info_cache[symbol] = data
        st.session_state.last_activity = datetime.now()

    @staticmethod
    def update_performance_metrics(query_type: str, response_time: float, cache_hit: bool = False):
        """更新性能指标"""
        metrics = st.session_state.performance_metrics

        metrics["total_queries"] += 1
        if cache_hit:
            metrics["cache_hits"] += 1
        else:
            metrics["akshare_calls"] += 1

        # 更新平均响应时间
        current_avg = metrics["avg_response_time"]
        total_queries = metrics["total_queries"]
        metrics["avg_response_time"] = (
            current_avg * (total_queries - 1) + response_time
        ) / total_queries

        # 记录查询历史（保持最近50条）
        metrics["query_history"].append(
            {
                "timestamp": datetime.now(),
                "query_type": query_type,
                "response_time": response_time,
                "cache_hit": cache_hit,
            }
        )

        if len(metrics["query_history"]) > 50:
            metrics["query_history"] = metrics["query_history"][-50:]

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """获取缓存统计信息"""
        metrics = st.session_state.performance_metrics

        return {
            "stock_data_count": len(st.session_state.stock_data_cache),
            "asset_info_count": len(st.session_state.asset_info_cache),
            "total_queries": metrics["total_queries"],
            "cache_hits": metrics["cache_hits"],
            "akshare_calls": metrics["akshare_calls"],
            "cache_hit_rate": (metrics["cache_hits"] / max(metrics["total_queries"], 1) * 100),
            "avg_response_time": metrics["avg_response_time"],
            "session_duration": datetime.now() - st.session_state.app_start_time,
            "last_activity": st.session_state.last_activity,
        }

    @staticmethod
    def clear_cache():
        """清空缓存"""
        st.session_state.stock_data_cache = {}
        st.session_state.asset_info_cache = {}
        st.session_state.performance_metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "akshare_calls": 0,
            "avg_response_time": 0,
            "query_history": [],
        }
        st.success("Cache cleared")

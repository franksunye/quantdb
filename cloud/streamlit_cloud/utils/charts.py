"""
QuantDB Frontend 图表工具

提供各种数据可视化图表的创建和配置功能。
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from .config import config


def create_price_chart(
    df: pd.DataFrame, title: str = "股票价格趋势", show_volume: bool = False
) -> go.Figure:
    """
    创建股票价格趋势图

    Args:
        df: 包含股票数据的DataFrame
        title: 图表标题
        show_volume: 是否显示成交量

    Returns:
        Plotly图表对象
    """
    if df.empty:
        # 创建空图表
        fig = go.Figure()
        fig.add_annotation(
            text="暂无数据",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray"),
        )
        return fig

    # 确保日期列存在并转换为datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    elif "trade_date" in df.columns:
        df["date"] = pd.to_datetime(df["trade_date"])

    # 创建子图
    if show_volume and "volume" in df.columns:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("价格", "成交量"),
            row_heights=[0.7, 0.3],
        )

        # 添加价格线
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["close"],
                mode="lines",
                name="收盘价",
                line=dict(color=config.COLORS["primary"], width=2),
                hovertemplate="日期: %{x}<br>收盘价: ¥%{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # 添加成交量柱状图
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                name="成交量",
                marker_color=config.COLORS["info"],
                hovertemplate="日期: %{x}<br>成交量: %{y:,.0f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

    else:
        # 只显示价格
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["close"],
                mode="lines",
                name="收盘价",
                line=dict(color=config.COLORS["primary"], width=2),
                hovertemplate="日期: %{x}<br>收盘价: ¥%{y:.2f}<extra></extra>",
            )
        )

    # 更新布局
    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="价格 (元)",
        hovermode="x unified",
        showlegend=True,
        height=config.CHART_HEIGHT,
        template="plotly_white",
    )

    return fig


def create_candlestick_chart(df: pd.DataFrame, title: str = "K线图") -> go.Figure:
    """
    创建K线图

    Args:
        df: 包含OHLC数据的DataFrame
        title: 图表标题

    Returns:
        Plotly图表对象
    """
    if df.empty or not all(
        col in df.columns for col in ["open", "high", "low", "close"]
    ):
        fig = go.Figure()
        fig.add_annotation(
            text="暂无K线数据",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray"),
        )
        return fig

    # 确保日期列存在
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    elif "trade_date" in df.columns:
        df["date"] = pd.to_datetime(df["trade_date"])

    fig = go.Figure(
        data=go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="K线",
            increasing_line_color=config.COLORS["success"],
            decreasing_line_color=config.COLORS["danger"],
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="价格 (元)",
        height=config.CHART_HEIGHT,
        template="plotly_white",
        xaxis_rangeslider_visible=False,
    )

    return fig


def create_volume_chart(df: pd.DataFrame, title: str = "成交量") -> go.Figure:
    """
    创建成交量图表

    Args:
        df: 包含成交量数据的DataFrame
        title: 图表标题

    Returns:
        Plotly图表对象
    """
    if df.empty or "volume" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无成交量数据",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray"),
        )
        return fig

    # 确保日期列存在
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    elif "trade_date" in df.columns:
        df["date"] = pd.to_datetime(df["trade_date"])

    fig = go.Figure(
        data=go.Bar(
            x=df["date"],
            y=df["volume"],
            name="成交量",
            marker_color=config.COLORS["info"],
            hovertemplate="日期: %{x}<br>成交量: %{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="成交量",
        height=config.CHART_HEIGHT,
        template="plotly_white",
        showlegend=False,
    )

    return fig


def create_returns_distribution(
    df: pd.DataFrame, title: str = "收益率分布"
) -> go.Figure:
    """
    创建收益率分布图

    Args:
        df: 包含价格数据的DataFrame
        title: 图表标题

    Returns:
        Plotly图表对象
    """
    if df.empty or "close" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无数据",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray"),
        )
        return fig

    # 计算日收益率
    returns = df["close"].pct_change().dropna() * 100

    fig = go.Figure(
        data=go.Histogram(
            x=returns,
            nbinsx=30,
            name="收益率分布",
            marker_color=config.COLORS["primary"],
            opacity=0.7,
            hovertemplate="收益率: %{x:.2f}%<br>频次: %{y}<extra></extra>",
        )
    )

    # 添加均值线
    mean_return = returns.mean()
    fig.add_vline(
        x=mean_return,
        line_dash="dash",
        line_color=config.COLORS["danger"],
        annotation_text=f"均值: {mean_return:.2f}%",
    )

    fig.update_layout(
        title=title,
        xaxis_title="日收益率 (%)",
        yaxis_title="频次",
        height=config.CHART_HEIGHT,
        template="plotly_white",
        showlegend=False,
    )

    return fig


def create_metrics_dashboard(metrics: Dict[str, Any]) -> None:
    """
    创建指标仪表板

    Args:
        metrics: 指标数据字典
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="最新价格",
            value=f"¥{metrics.get('latest_price', 0):.2f}",
            delta=f"{metrics.get('price_change', 0):.2f}%",
        )

    with col2:
        st.metric(
            label="最高价", value=f"¥{metrics.get('high_price', 0):.2f}", delta=None
        )

    with col3:
        st.metric(
            label="最低价", value=f"¥{metrics.get('low_price', 0):.2f}", delta=None
        )

    with col4:
        st.metric(
            label="平均价格", value=f"¥{metrics.get('avg_price', 0):.2f}", delta=None
        )


def calculate_basic_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    计算基础统计指标

    Args:
        df: 股票数据DataFrame

    Returns:
        指标字典
    """
    if df.empty or "close" not in df.columns:
        return {}

    latest_price = df["close"].iloc[-1] if len(df) > 0 else 0
    previous_price = df["close"].iloc[-2] if len(df) > 1 else latest_price
    price_change = (
        ((latest_price - previous_price) / previous_price * 100)
        if previous_price != 0
        else 0
    )

    return {
        "latest_price": latest_price,
        "high_price": df["close"].max(),
        "low_price": df["close"].min(),
        "avg_price": df["close"].mean(),
        "price_change": price_change,
        "volatility": df["close"].std(),
        "total_volume": df.get("volume", pd.Series()).sum(),
    }


def format_large_number(num: float) -> str:
    """
    格式化大数字显示

    Args:
        num: 数字

    Returns:
        格式化后的字符串
    """
    if num >= 1e8:
        return f"{num/1e8:.2f}亿"
    elif num >= 1e4:
        return f"{num/1e4:.2f}万"
    else:
        return f"{num:.2f}"


def create_performance_comparison_chart(
    cache_time: float, akshare_time: float
) -> go.Figure:
    """
    创建性能对比图表

    Args:
        cache_time: 缓存响应时间(ms)
        akshare_time: AKShare响应时间(ms)

    Returns:
        Plotly图表对象
    """
    categories = ["缓存查询", "AKShare直接调用"]
    times = [cache_time, akshare_time]
    colors = [config.COLORS["success"], config.COLORS["danger"]]

    fig = go.Figure(
        data=go.Bar(
            x=categories,
            y=times,
            marker_color=colors,
            text=[f"{t:.1f}ms" for t in times],
            textposition="auto",
            hovertemplate="%{x}<br>响应时间: %{y:.1f}ms<extra></extra>",
        )
    )

    # 计算性能提升
    improvement = (
        ((akshare_time - cache_time) / akshare_time * 100) if akshare_time > 0 else 0
    )

    fig.update_layout(
        title=f"性能对比 - 缓存提升 {improvement:.1f}%",
        xaxis_title="查询方式",
        yaxis_title="响应时间 (ms)",
        height=config.CHART_HEIGHT,
        template="plotly_white",
        showlegend=False,
    )

    return fig


def create_data_coverage_timeline(df: pd.DataFrame) -> go.Figure:
    """
    创建数据覆盖时间轴图表

    Args:
        df: 包含日期数据的DataFrame

    Returns:
        Plotly图表对象
    """
    if df.empty or "date" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无数据覆盖信息",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="gray"),
        )
        return fig

    # 确保日期列是datetime类型
    df["date"] = pd.to_datetime(df["date"])

    # 按月统计数据量
    df["year_month"] = df["date"].dt.to_period("M")
    monthly_counts = df.groupby("year_month").size().reset_index(name="count")
    monthly_counts["date"] = monthly_counts["year_month"].dt.start_time

    fig = go.Figure(
        data=go.Bar(
            x=monthly_counts["date"],
            y=monthly_counts["count"],
            name="月度数据量",
            marker_color=config.COLORS["primary"],
            hovertemplate="%{x|%Y-%m}<br>数据量: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        title="数据覆盖时间轴",
        xaxis_title="时间",
        yaxis_title="数据量",
        height=config.CHART_HEIGHT,
        template="plotly_white",
        showlegend=False,
    )

    return fig


def create_cache_hit_pie_chart(cache_hits: int, cache_misses: int) -> go.Figure:
    """
    创建缓存命中率饼图

    Args:
        cache_hits: 缓存命中次数
        cache_misses: 缓存未命中次数

    Returns:
        Plotly图表对象
    """
    labels = ["缓存命中", "缓存未命中"]
    values = [cache_hits, cache_misses]
    colors = [config.COLORS["success"], config.COLORS["danger"]]

    total = cache_hits + cache_misses
    hit_rate = (cache_hits / total * 100) if total > 0 else 0

    fig = go.Figure(
        data=go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hovertemplate="%{label}<br>次数: %{value}<br>占比: %{percent}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"缓存命中率 - {hit_rate:.1f}%",
        height=config.CHART_HEIGHT,
        template="plotly_white",
    )

    return fig


class StockChartBuilder:
    """股票图表构建器 - 云端版本"""

    @staticmethod
    def create_price_trend_chart(
        df: pd.DataFrame, symbol: str, name: str = None
    ) -> go.Figure:
        """创建价格趋势图"""
        return create_price_chart(df, f"{name or symbol} - 收盘价趋势")

    @staticmethod
    def create_volume_chart(
        df: pd.DataFrame, symbol: str, name: str = None
    ) -> go.Figure:
        """创建成交量图表"""
        return create_volume_chart(df, f"{name or symbol} - 成交量")

    @staticmethod
    def create_candlestick_chart(
        df: pd.DataFrame, symbol: str, name: str = None
    ) -> go.Figure:
        """创建K线图"""
        return create_candlestick_chart(df, f"{name or symbol} - K线图")

    @staticmethod
    def create_returns_chart(
        df: pd.DataFrame, symbol: str, name: str = None
    ) -> go.Figure:
        """创建收益率图表"""
        return create_returns_distribution(df, f"{name or symbol} - 收益率分布")

    @staticmethod
    def create_performance_comparison_chart(cache_stats: Dict[str, Any]) -> go.Figure:
        """创建性能对比图表"""
        categories = ["缓存命中", "AKShare调用"]
        values = [cache_stats.get("cache_hits", 0), cache_stats.get("akshare_calls", 0)]
        colors = ["#2ca02c", "#ff7f0e"]

        fig = px.pie(
            values=values,
            names=categories,
            title="查询来源分布",
            color_discrete_sequence=colors,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>次数: %{value}<br>占比: %{percent}<extra></extra>",
        )

        fig.update_layout(height=300)

        return fig

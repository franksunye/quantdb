"""
Financial data models for QuantDB core.

This module contains models for storing financial summary and indicator data
with intelligent caching strategies.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..database.connection import Base


class FinancialSummary(Base):
    """
    Financial summary data model for storing quarterly financial metrics.

    This model stores data from AKShare's stock_financial_abstract interface,
    which provides key financial metrics across multiple quarters.
    """

    __tablename__ = "financial_summary"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"), index=True)
    symbol = Column(String(10), index=True)

    # Financial metrics - core indicators
    net_profit = Column(Float, comment="归母净利润")
    total_revenue = Column(Float, comment="营业总收入")
    operating_cost = Column(Float, comment="营业成本")
    gross_profit = Column(Float, comment="毛利润")
    operating_profit = Column(Float, comment="营业利润")

    # Balance sheet indicators
    total_assets = Column(Float, comment="总资产")
    total_liabilities = Column(Float, comment="总负债")
    shareholders_equity = Column(Float, comment="股东权益")

    # Cash flow indicators
    operating_cash_flow = Column(Float, comment="经营活动现金流")
    investing_cash_flow = Column(Float, comment="投资活动现金流")
    financing_cash_flow = Column(Float, comment="筹资活动现金流")

    # Financial ratios
    roe = Column(Float, comment="净资产收益率")
    roa = Column(Float, comment="总资产收益率")
    gross_margin = Column(Float, comment="毛利率")
    net_margin = Column(Float, comment="净利率")

    # Period information
    report_period = Column(String(8), comment="报告期 YYYYMMDD")
    report_type = Column(String(10), comment="报告类型: Q1, Q2, Q3, Q4")

    # Raw data storage for flexibility
    raw_data = Column(JSON, comment="原始财务数据JSON")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="financial_summaries")

    @classmethod
    def from_akshare_data(
        cls, symbol: str, asset_id: Optional[int], akshare_df
    ) -> List["FinancialSummary"]:
        """
        Create FinancialSummary instances from AKShare financial abstract data.

        Args:
            symbol: Stock symbol
            asset_id: Asset ID from assets table
            akshare_df: DataFrame from stock_financial_abstract

        Returns:
            List of FinancialSummary instances
        """
        summaries = []

        if akshare_df.empty:
            return summaries

        # Get date columns (exclude '选项' and '指标' columns)
        date_columns = [
            col for col in akshare_df.columns if col not in ["选项", "指标"]
        ]

        # Process each quarter
        for date_col in date_columns[:8]:  # Latest 8 quarters
            try:
                # Create a summary for this quarter
                summary = cls(
                    symbol=symbol,
                    asset_id=asset_id,
                    report_period=date_col,
                    report_type=cls._get_report_type(date_col),
                )

                # Extract financial metrics
                for _, row in akshare_df.iterrows():
                    indicator = row["指标"]
                    value = row.get(date_col)

                    if value is not None and not pd.isna(value):
                        # Map Chinese indicators to model fields
                        if indicator == "归母净利润":
                            summary.net_profit = float(value)
                        elif indicator == "营业总收入":
                            summary.total_revenue = float(value)
                        elif indicator == "营业成本":
                            summary.operating_cost = float(value)
                        elif indicator == "毛利润":
                            summary.gross_profit = float(value)
                        elif indicator == "营业利润":
                            summary.operating_profit = float(value)
                        elif indicator == "总资产":
                            summary.total_assets = float(value)
                        elif indicator == "总负债":
                            summary.total_liabilities = float(value)
                        elif indicator == "股东权益":
                            summary.shareholders_equity = float(value)
                        elif indicator == "经营活动现金流":
                            summary.operating_cash_flow = float(value)
                        elif indicator == "净资产收益率":
                            summary.roe = float(value)
                        elif indicator == "总资产收益率":
                            summary.roa = float(value)
                        elif indicator == "毛利率":
                            summary.gross_margin = float(value)
                        elif indicator == "净利率":
                            summary.net_margin = float(value)

                # Calculate derived metrics
                if summary.total_revenue and summary.operating_cost:
                    summary.gross_profit = (
                        summary.total_revenue - summary.operating_cost
                    )
                    summary.gross_margin = (
                        summary.gross_profit / summary.total_revenue
                    ) * 100

                if summary.net_profit and summary.total_revenue:
                    summary.net_margin = (
                        summary.net_profit / summary.total_revenue
                    ) * 100

                # Store raw data
                quarter_data = {}
                for _, row in akshare_df.iterrows():
                    quarter_data[row["指标"]] = row.get(date_col)
                summary.raw_data = quarter_data

                summaries.append(summary)

            except Exception as e:
                continue  # Skip problematic quarters

        return summaries

    @staticmethod
    def _get_report_type(date_str: str) -> str:
        """Get report type from date string."""
        if date_str.endswith("0331"):
            return "Q1"
        elif date_str.endswith("0630"):
            return "Q2"
        elif date_str.endswith("0930"):
            return "Q3"
        elif date_str.endswith("1231"):
            return "Q4"
        else:
            return "Unknown"


class FinancialIndicators(Base):
    """
    Financial indicators model for storing detailed financial analysis metrics.

    This model stores data from AKShare's stock_financial_analysis_indicator interface.
    """

    __tablename__ = "financial_indicators"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.asset_id"), index=True)
    symbol = Column(String(10), index=True)

    # Profitability indicators
    eps = Column(Float, comment="每股收益")
    pe_ratio = Column(Float, comment="市盈率")
    pb_ratio = Column(Float, comment="市净率")
    ps_ratio = Column(Float, comment="市销率")

    # Growth indicators
    revenue_growth = Column(Float, comment="营收增长率")
    profit_growth = Column(Float, comment="利润增长率")
    eps_growth = Column(Float, comment="每股收益增长率")

    # Financial health indicators
    debt_to_equity = Column(Float, comment="资产负债率")
    current_ratio = Column(Float, comment="流动比率")
    quick_ratio = Column(Float, comment="速动比率")

    # Efficiency indicators
    asset_turnover = Column(Float, comment="总资产周转率")
    inventory_turnover = Column(Float, comment="存货周转率")
    receivables_turnover = Column(Float, comment="应收账款周转率")

    # Period information
    report_period = Column(String(8), comment="报告期 YYYYMMDD")

    # Raw data storage
    raw_data = Column(JSON, comment="原始指标数据JSON")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="financial_indicators")


class FinancialDataCache(Base):
    """
    Cache management for financial data with intelligent TTL strategies.

    Financial data updates less frequently than stock prices, so we can use
    longer cache periods (daily for summary, weekly for indicators).
    """

    __tablename__ = "financial_data_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True)
    data_type = Column(String(20), index=True, comment="summary or indicators")

    # Cache metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    cache_hit_count = Column(Integer, default=0)
    data_source = Column(String(50), default="akshare")

    # Cache validity
    expires_at = Column(DateTime)
    is_valid = Column(Integer, default=1)  # 1=valid, 0=invalid

    @classmethod
    def is_cache_valid(cls, symbol: str, data_type: str, db_session) -> bool:
        """
        Check if cached financial data is still valid.

        Args:
            symbol: Stock symbol
            data_type: 'summary' or 'indicators'
            db_session: Database session

        Returns:
            True if cache is valid, False otherwise
        """
        cache_record = (
            db_session.query(cls)
            .filter(cls.symbol == symbol, cls.data_type == data_type, cls.is_valid == 1)
            .first()
        )

        if not cache_record:
            return False

        return datetime.utcnow() < cache_record.expires_at

    @classmethod
    def update_cache_record(cls, symbol: str, data_type: str, db_session):
        """Update cache record after successful data fetch."""
        # Set cache TTL based on data type
        if data_type == "summary":
            ttl_hours = 24  # Daily update for summary
        else:
            ttl_hours = 168  # Weekly update for indicators

        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Update existing record or create new one
        cache_record = (
            db_session.query(cls)
            .filter(cls.symbol == symbol, cls.data_type == data_type)
            .first()
        )

        if cache_record:
            cache_record.last_updated = datetime.utcnow()
            cache_record.expires_at = expires_at
            cache_record.cache_hit_count += 1
        else:
            cache_record = cls(
                symbol=symbol,
                data_type=data_type,
                expires_at=expires_at,
                cache_hit_count=1,
            )
            db_session.add(cache_record)

        db_session.commit()

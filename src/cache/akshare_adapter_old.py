# src/cache/akshare_adapter.py
"""
AKShare adapter for the Reservoir Cache mechanism.

This module provides a unified interface for AKShare API calls,
with error handling, retry logic, and integration with the cache engine.
"""

import re
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from src.logger import logger

def with_cache(ttl: Optional[int] = None, freshness_requirement: str = "default"):
    """
    Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds. If None, the data doesn't expire.
        freshness_requirement: The freshness requirement for cached data.
            Can be "strict", "normal", "relaxed", or "default".

    Returns:
        A decorator function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = self.cache_engine.generate_key(
                func.__name__, *args, **kwargs
            )

            # Check if data is in cache and fresh
            if self.freshness_tracker.is_fresh(cache_key, freshness_requirement):
                cached_data = self.cache_engine.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {func.__name__}({args}, {kwargs})")
                    return cached_data

            # If not in cache or not fresh, call the function
            logger.debug(f"Cache miss for {func.__name__}({args}, {kwargs})")
            result = func(self, *args, **kwargs)

            # Store result in cache
            self.cache_engine.set(cache_key, result, ttl)
            self.freshness_tracker.mark_updated(cache_key, ttl)

            return result
        return wrapper
    return decorator

class AKShareAdapter:
    """
    Adapter for AKShare API calls.

    This class provides methods for accessing AKShare data with caching,
    error handling, and retry logic.
    """

    def __init__(
        self,
        cache_engine: Optional[CacheEngine] = None,
        freshness_tracker: Optional[FreshnessTracker] = None
    ):
        """
        Initialize the AKShare adapter.

        Args:
            cache_engine: The cache engine to use. If None, creates a new one.
            freshness_tracker: The freshness tracker to use. If None, creates a new one.
        """
        self.cache_engine = cache_engine or CacheEngine()
        self.freshness_tracker = freshness_tracker or FreshnessTracker()
        logger.info("AKShare adapter initialized")

    @retry(
        stop=stop_after_attempt(5),  # 增加重试次数
        wait=wait_exponential(multiplier=1, min=2, max=30),  # 增加等待时间
        reraise=True
    )
    def _safe_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Safely call an AKShare function with retry logic.

        Args:
            func: The AKShare function to call.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The result of the function call.

        Raises:
            Exception: If the function call fails after all retries.
        """
        try:
            # 记录详细的调用信息
            arg_str = ', '.join([str(arg) for arg in args])
            kwarg_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            logger.info(f"Calling AKShare function {func.__name__}({arg_str}, {kwarg_str})")

            # 执行函数调用
            result = func(*args, **kwargs)

            # 检查结果是否为DataFrame且为空
            if isinstance(result, pd.DataFrame) and result.empty:
                logger.warning(f"AKShare function {func.__name__} returned empty DataFrame")
                # 记录更多诊断信息
                logger.warning(f"Empty DataFrame returned for args={args}, kwargs={kwargs}")
            elif isinstance(result, pd.DataFrame):
                logger.info(f"AKShare function {func.__name__} returned DataFrame with {len(result)} rows")
                # 记录数据范围信息（如果是时间序列数据）
                if 'date' in result.columns:
                    logger.info(f"Date range: {result['date'].min()} to {result['date'].max()}")

            return result
        except Exception as e:
            logger.error(f"Error calling AKShare function {func.__name__}: {e}")
            logger.error(f"Function arguments: args={args}, kwargs={kwargs}")
            # 记录更详细的错误信息
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            # 记录网络相关错误的更多信息
            if "ConnectionError" in str(e) or "Timeout" in str(e) or "HTTPError" in str(e):
                logger.error(f"Network-related error detected. This might be due to connectivity issues or API changes.")

            # 记录可能的API变更信息
            if "KeyError" in str(e) or "IndexError" in str(e) or "ValueError" in str(e):
                logger.error(f"Possible API change detected. The structure of the response may have changed.")

            raise

    @with_cache(ttl=86400)  # Cache for 24 hours
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "",
        use_mock_data: bool = False,
        period: str = "daily"
    ) -> pd.DataFrame:
        """
        Get stock historical data.

        Args:
            symbol: Stock symbol.
            start_date: Start date in format YYYYMMDD.
            end_date: End date in format YYYYMMDD.
            adjust: Price adjustment method. Options are:
                   "" (empty string): No adjustment
                   "qfq": Forward adjustment
                   "hfq": Backward adjustment
            use_mock_data: If True, use mock data when AKShare returns empty data.
            period: Data frequency. Options are "daily", "weekly", "monthly".

        Returns:
            DataFrame with stock data.
        """
        logger.info(f"Getting stock data for {symbol} from {start_date} to {end_date} with adjust={adjust}, period={period}")

        # 验证参数
        if not symbol:
            logger.error("Symbol cannot be empty")
            raise ValueError("Symbol cannot be empty")

        # 验证period参数
        valid_periods = ["daily", "weekly", "monthly"]
        if period not in valid_periods:
            logger.error(f"Invalid period: {period}. Valid options are: {valid_periods}")
            raise ValueError(f"Invalid period: {period}. Valid options are: {valid_periods}")

        # 验证adjust参数
        valid_adjusts = ["", "qfq", "hfq"]
        if adjust not in valid_adjusts:
            logger.error(f"Invalid adjust: {adjust}. Valid options are: {valid_adjusts}")
            raise ValueError(f"Invalid adjust: {adjust}. Valid options are: {valid_adjusts}")

        # Validate symbol format
        if not self._validate_symbol(symbol):
            logger.error(f"Invalid symbol format: {symbol}")
            if use_mock_data:
                logger.warning(f"Using mock data for invalid symbol: {symbol}")
                # 设置默认日期
                if end_date is None:
                    end_date = datetime.now().strftime('%Y%m%d')
                if start_date is None:
                    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
                # 验证和格式化日期
                start_date = self._validate_and_format_date(start_date)
                end_date = self._validate_and_format_date(end_date)
                return self._generate_mock_stock_data(symbol, start_date, end_date, adjust, period)
            else:
                raise ValueError(f"Invalid symbol format: {symbol}. Symbol should be a 6-digit number.")

        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
            logger.info(f"No end date provided, using current date: {end_date}")

        if start_date is None:
            # 根据period调整默认的开始日期
            if period == "daily":
                # 默认获取1年的日线数据
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            elif period == "weekly":
                # 默认获取2年的周线数据
                start_date = (datetime.now() - timedelta(days=2*365)).strftime('%Y%m%d')
            else:  # monthly
                # 默认获取5年的月线数据
                start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
            logger.info(f"No start date provided, using default for {period} period: {start_date}")

        # Validate and format dates
        original_start_date = start_date
        original_end_date = end_date

        start_date = self._validate_and_format_date(start_date)
        end_date = self._validate_and_format_date(end_date)

        # Log date transformations for debugging
        if original_start_date != start_date:
            logger.info(f"Start date transformed from {original_start_date} to {start_date}")
        if original_end_date != end_date:
            logger.info(f"End date transformed from {original_end_date} to {end_date}")

        # Check if date range is valid
        if self._is_future_date(end_date):
            logger.warning(f"End date {end_date} is in the future. Setting to today.")
            end_date = datetime.now().strftime('%Y%m%d')

        if self._compare_dates(start_date, end_date) > 0:
            logger.error(f"Start date {start_date} is after end date {end_date}")
            raise ValueError(f"Start date {start_date} cannot be after end date {end_date}")

        # 保存原始符号以便回退
        original_symbol = symbol

        # 标准化股票代码 - 移除市场前缀和后缀，只保留数字部分
        # 因为 stock_zh_a_hist 函数需要的是不带前缀的纯数字代码

        # 移除可能的后缀
        if "." in symbol:
            symbol = symbol.split(".")[0]

        # 移除可能的市场前缀
        if symbol.lower().startswith("sh") or symbol.lower().startswith("sz"):
            symbol = symbol[2:]

        logger.info(f"Standardized symbol for AKShare: {symbol}")

        # 使用官方文档推荐的 stock_zh_a_hist 函数获取数据
        try:
            logger.info(f"Getting data using stock_zh_a_hist for {symbol} with period={period}, adjust={adjust}")

            df = self._safe_call(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if not df.empty:
                logger.info(f"Successfully retrieved {len(df)} rows of data for {symbol} using stock_zh_a_hist")

                # 标准化列名
                df = self._standardize_stock_data(df)

                # 验证数据完整性
                if self._validate_stock_data(df, symbol, start_date, end_date):
                    return df
                else:
                    logger.warning(f"Data validation failed for {symbol}. Will try alternative methods.")
            else:
                logger.warning(f"stock_zh_a_hist returned empty data for {symbol}")
        except Exception as e:
            logger.error(f"Error getting data using stock_zh_a_hist for {symbol}: {e}")

        # 如果 stock_zh_a_hist 失败，尝试使用 stock_zh_a_hist_tx 函数（腾讯数据源）
        try:
            # 为腾讯数据源准备带前缀的代码
            tx_symbol = original_symbol

            # 如果没有市场前缀，添加前缀
            if not (tx_symbol.lower().startswith("sh") or tx_symbol.lower().startswith("sz")):
                # 根据股票代码判断市场
                if tx_symbol.startswith("6"):
                    tx_symbol = f"sh{tx_symbol}"
                elif tx_symbol.startswith("0") or tx_symbol.startswith("3"):
                    tx_symbol = f"sz{tx_symbol}"
                else:
                    # 如果无法确定，尝试上海市场
                    tx_symbol = f"sh{tx_symbol}"
                    logger.warning(f"Cannot determine market for {original_symbol}, trying with 'sh' prefix")

            logger.info(f"Trying to get data using stock_zh_a_hist_tx for {tx_symbol}")

            df = self._safe_call(
                ak.stock_zh_a_hist_tx,
                symbol=tx_symbol
            )

            if not df.empty:
                logger.info(f"Successfully retrieved {len(df)} rows of data for {tx_symbol} using stock_zh_a_hist_tx")

                # 过滤日期
                df["date"] = pd.to_datetime(df["date"])
                start_date_dt = pd.to_datetime(start_date, format="%Y%m%d")
                end_date_dt = pd.to_datetime(end_date, format="%Y%m%d")

                filtered_df = df[(df["date"] >= start_date_dt) & (df["date"] <= end_date_dt)]

                if not filtered_df.empty:
                    logger.info(f"After date filtering, {len(filtered_df)} rows remain")

                    # 应用复权（如果需要）
                    if adjust and adjust in ["qfq", "hfq"]:
                        logger.info(f"Applying price adjustment: {adjust}")
                        logger.warning(f"Price adjustment '{adjust}' is not directly supported with stock_zh_a_hist_tx. Returning unadjusted data.")

                    # 标准化列名
                    filtered_df = self._standardize_stock_data(filtered_df)

                    # 如果需要周线或月线数据，但获取的是日线数据，进行转换
                    if period != "daily":
                        logger.info(f"Converting daily data to {period} data")
                        filtered_df = self._convert_to_period(filtered_df, period)

                    # 验证数据完整性
                    if self._validate_stock_data(filtered_df, tx_symbol, start_date, end_date):
                        return filtered_df
                    else:
                        logger.warning(f"Data validation failed for {tx_symbol}. Will try alternative methods.")
                else:
                    logger.warning(f"No data found for {tx_symbol} in date range {start_date} to {end_date}")
            else:
                logger.warning(f"stock_zh_a_hist_tx returned empty data for {tx_symbol}")
        except Exception as e:
            logger.error(f"Error getting data using stock_zh_a_hist_tx for {tx_symbol}: {e}")

        # 如果是指数，尝试使用 stock_zh_index_daily 函数
        try:
            # 检查是否可能是指数
            if (symbol.startswith("000") or symbol.startswith("399") or
                symbol.startswith("50") or symbol.startswith("51") or
                symbol.startswith("60") or symbol == "000001" or
                symbol == "399001" or symbol == "000300"):

                # 为指数数据源准备带前缀的代码
                index_symbol = original_symbol

                # 如果没有市场前缀，添加前缀
                if not (index_symbol.lower().startswith("sh") or index_symbol.lower().startswith("sz")):
                    # 根据指数代码判断市场
                    if index_symbol.startswith("0") or index_symbol.startswith("9") or index_symbol.startswith("5"):
                        index_symbol = f"sh{index_symbol}"
                    elif index_symbol.startswith("3"):
                        index_symbol = f"sz{index_symbol}"
                    else:
                        # 默认使用上海市场
                        index_symbol = f"sh{index_symbol}"

                logger.info(f"Symbol {symbol} might be an index, trying stock_zh_index_daily with {index_symbol}")

                df = self._safe_call(
                    ak.stock_zh_index_daily,
                    symbol=index_symbol
                )

                if not df.empty:
                    logger.info(f"Successfully retrieved {len(df)} rows of data for index {index_symbol}")

                    # 过滤日期
                    df["date"] = pd.to_datetime(df["date"])
                    start_date_dt = pd.to_datetime(start_date, format="%Y%m%d")
                    end_date_dt = pd.to_datetime(end_date, format="%Y%m%d")

                    filtered_df = df[(df["date"] >= start_date_dt) & (df["date"] <= end_date_dt)]

                    if not filtered_df.empty:
                        logger.info(f"After date filtering, {len(filtered_df)} rows remain")

                        # 标准化列名
                        filtered_df = self._standardize_stock_data(filtered_df)

                        # 如果需要周线或月线数据，但获取的是日线数据，进行转换
                        if period != "daily":
                            logger.info(f"Converting daily data to {period} data")
                            filtered_df = self._convert_to_period(filtered_df, period)

                        # 验证数据完整性
                        if self._validate_stock_data(filtered_df, index_symbol, start_date, end_date):
                            return filtered_df
                        else:
                            logger.warning(f"Data validation failed for index {index_symbol}. Will try alternative methods.")
                    else:
                        logger.warning(f"No data found for index {index_symbol} in date range {start_date} to {end_date}")
                else:
                    logger.warning(f"stock_zh_index_daily returned empty data for {index_symbol}")
        except Exception as e:
            logger.error(f"Error getting data using stock_zh_index_daily for index: {e}")

        # 如果所有数据源都失败，并且允许使用模拟数据
        if use_mock_data:
            logger.warning(f"All data sources failed for {symbol}. Using mock data as requested.")
            return self._generate_mock_stock_data(symbol, start_date, end_date, adjust, period)

        # 如果所有方法都失败，返回空DataFrame
        logger.error(f"All methods failed to get data for {symbol}. Returning empty DataFrame.")
        return pd.DataFrame()

    @with_cache(ttl=86400)  # Cache for 24 hours
    def get_index_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get index historical data.

        Args:
            symbol: Index symbol.
            start_date: Start date in format YYYYMMDD.
            end_date: End date in format YYYYMMDD.

        Returns:
            DataFrame with index data.
        """
        logger.info(f"Getting index data for {symbol} from {start_date} to {end_date}")

        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        if start_date is None:
            # Default to 1 year of data
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        # Validate and format dates
        start_date = self._validate_and_format_date(start_date)
        end_date = self._validate_and_format_date(end_date)

        # Check if date range is valid
        if self._is_future_date(end_date):
            logger.warning(f"End date {end_date} is in the future. Setting to today.")
            end_date = datetime.now().strftime('%Y%m%d')

        if self._compare_dates(start_date, end_date) > 0:
            logger.error(f"Start date {start_date} is after end date {end_date}")
            raise ValueError(f"Start date {start_date} cannot be after end date {end_date}")

        # 标准化指数代码
        # 移除可能的后缀
        if "." in symbol:
            symbol = symbol.split(".")[0]

        # 添加市场前缀（如果没有）
        if not (symbol.startswith("sh") or symbol.startswith("sz") or
                symbol.startswith("SH") or symbol.startswith("SZ")):
            # 根据指数代码判断市场
            if symbol.startswith("0") or symbol.startswith("9"):
                symbol = f"sh{symbol}"
            elif symbol.startswith("3"):
                symbol = f"sz{symbol}"
            else:
                # 默认使用上海市场
                symbol = f"sh{symbol}"

        logger.info(f"Standardized index symbol: {symbol}")

        # 尝试使用 stock_zh_index_daily 函数获取数据
        try:
            logger.info(f"Trying to get data using stock_zh_index_daily for {symbol}")

            df = self._safe_call(
                ak.stock_zh_index_daily,
                symbol=symbol
            )

            if not df.empty:
                logger.info(f"Successfully retrieved {len(df)} rows of data for index {symbol}")

                # 过滤日期
                df["date"] = pd.to_datetime(df["date"])
                start_date_dt = pd.to_datetime(start_date, format="%Y%m%d")
                end_date_dt = pd.to_datetime(end_date, format="%Y%m%d")

                filtered_df = df[(df["date"] >= start_date_dt) & (df["date"] <= end_date_dt)]

                if not filtered_df.empty:
                    logger.info(f"After date filtering, {len(filtered_df)} rows remain")

                    # 标准化列名
                    filtered_df = self._standardize_index_data(filtered_df)
                    return filtered_df
                else:
                    logger.warning(f"No data found for index {symbol} in date range {start_date} to {end_date}")
            else:
                logger.warning(f"stock_zh_index_daily returned empty data for {symbol}")

        except Exception as e:
            logger.error(f"Error getting data using stock_zh_index_daily for {symbol}: {e}")

            # 尝试使用备用方法
            try:
                logger.info(f"Trying alternative method for index {symbol}")

                # 尝试使用 stock_zh_index_daily_tx 函数（腾讯数据源）
                df = self._safe_call(
                    ak.stock_zh_index_daily_tx,
                    symbol=symbol
                )

                if not df.empty:
                    logger.info(f"Successfully retrieved {len(df)} rows of data for index {symbol} using stock_zh_index_daily_tx")

                    # 过滤日期
                    df["date"] = pd.to_datetime(df["date"])
                    start_date_dt = pd.to_datetime(start_date, format="%Y%m%d")
                    end_date_dt = pd.to_datetime(end_date, format="%Y%m%d")

                    filtered_df = df[(df["date"] >= start_date_dt) & (df["date"] <= end_date_dt)]

                    if not filtered_df.empty:
                        logger.info(f"After date filtering, {len(filtered_df)} rows remain")

                        # 标准化列名
                        filtered_df = self._standardize_index_data(filtered_df)
                        return filtered_df
                    else:
                        logger.warning(f"No data found for index {symbol} in date range {start_date} to {end_date}")
                else:
                    logger.warning(f"stock_zh_index_daily_tx returned empty data for {symbol}")

            except Exception as alt_e:
                logger.error(f"Alternative method failed for index {symbol}: {alt_e}")

        # 如果所有方法都失败，返回空DataFrame
        logger.error(f"All methods failed to get data for index {symbol}. Returning empty DataFrame.")
        return pd.DataFrame()

    @with_cache(ttl=86400 * 7)  # Cache for 7 days
    def get_stock_list(self) -> pd.DataFrame:
        """
        Get a list of all stocks.

        Returns:
            DataFrame with stock information.
        """
        logger.info("Getting stock list")

        # Call AKShare function with retry logic
        df = self._safe_call(ak.stock_info_a_code_name)

        return df

    @with_cache(ttl=86400 * 7)  # Cache for 7 days
    def get_index_list(self) -> pd.DataFrame:
        """
        Get a list of all indices.

        Returns:
            DataFrame with index information.
        """
        logger.info("Getting index list")

        # Call AKShare function with retry logic
        df = self._safe_call(ak.index_stock_info)

        return df

    @with_cache(ttl=86400)  # Cache for 24 hours
    def get_index_constituents(self, index_symbol: str) -> pd.DataFrame:
        """
        Get the constituents of an index.

        Args:
            index_symbol: Index symbol.

        Returns:
            DataFrame with constituent information.
        """
        logger.info(f"Getting constituents for index {index_symbol}")

        # Call AKShare function with retry logic
        df = self._safe_call(ak.index_stock_cons_sina, symbol=index_symbol)

        return df

    def _standardize_stock_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize stock data column names.

        Args:
            df: DataFrame with stock data.

        Returns:
            DataFrame with standardized column names.
        """
        # 记录原始列名，用于调试
        logger.debug(f"Original columns: {df.columns.tolist()}")

        # Map of AKShare column names to standardized names (支持多种可能的列名)
        column_map = {
            # 日期列
            '日期': 'date',
            'date': 'date',
            '时间': 'date',
            'time': 'date',
            'trade_date': 'date',
            'trading_date': 'date',

            # 开盘价列
            '开盘': 'open',
            'open': 'open',
            '开盘价': 'open',
            '今开': 'open',

            # 收盘价列
            '收盘': 'close',
            'close': 'close',
            '收盘价': 'close',
            '最新价': 'close',

            # 最高价列
            '最高': 'high',
            'high': 'high',
            '最高价': 'high',

            # 最低价列
            '最低': 'low',
            'low': 'low',
            '最低价': 'low',

            # 成交量列
            '成交量': 'volume',
            'volume': 'volume',
            '成交股数': 'volume',
            '成交数量': 'volume',

            # 成交额列
            '成交额': 'turnover',
            'turnover': 'turnover',
            '成交金额': 'turnover',

            # 振幅列
            '振幅': 'amplitude',
            'amplitude': 'amplitude',

            # 涨跌幅列
            '涨跌幅': 'pct_change',
            'pct_change': 'pct_change',
            '涨跌(%)': 'pct_change',
            '涨跌百分比': 'pct_change',
            'change_pct': 'pct_change',

            # 涨跌额列
            '涨跌额': 'change',
            'change': 'change',
            '涨跌': 'change',

            # 换手率列
            '换手率': 'turnover_rate',
            'turnover_rate': 'turnover_rate',
            '换手(%)': 'turnover_rate'
        }

        # 重命名存在的列
        rename_dict = {k: v for k, v in column_map.items() if k in df.columns}
        df = df.rename(columns=rename_dict)

        # 记录标准化后的列名，用于调试
        logger.debug(f"Standardized columns: {df.columns.tolist()}")

        # 确保必要的列存在，如果不存在则添加空列
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Required column '{col}' not found in DataFrame. Adding empty column.")
                df[col] = pd.NA

        # 确保日期列格式为YYYY-MM-DD
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            except Exception as e:
                logger.error(f"Error formatting date column: {e}")
                # 如果转换失败，尝试不同的格式
                try:
                    # 尝试处理Unix时间戳
                    if df['date'].dtype == 'int64' or df['date'].dtype == 'float64':
                        df['date'] = pd.to_datetime(df['date'], unit='s').dt.strftime('%Y-%m-%d')
                    else:
                        # 尝试多种日期格式
                        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
                except Exception as e2:
                    logger.error(f"Failed to format date column after retry: {e2}")

        # 确保数值列为浮点型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'turnover', 'amplitude', 'pct_change', 'change', 'turnover_rate']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    logger.error(f"Error converting column '{col}' to numeric: {e}")

        return df

    def _standardize_index_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize index data column names.

        Args:
            df: DataFrame with index data.

        Returns:
            DataFrame with standardized column names.
        """
        # 直接复用股票数据的标准化方法，因为列名映射已经足够全面
        return self._standardize_stock_data(df)

    def _validate_symbol(self, symbol: str) -> bool:
        """
        Validate stock symbol format.

        Args:
            symbol: Stock symbol to validate.

        Returns:
            True if the symbol is valid, False otherwise.
        """
        if not symbol:
            return False

        # 尝试清理和标准化股票代码
        try:
            # 移除所有非数字字符
            cleaned_symbol = re.sub(r'\D', '', symbol)

            # 如果清理后的代码长度为6，则认为是有效的
            if len(cleaned_symbol) == 6:
                if symbol != cleaned_symbol:
                    logger.warning(f"Symbol {symbol} was cleaned to {cleaned_symbol}")
                return True

            # 特殊情况：如果原始代码以'sh'或'sz'开头，后跟6位数字，也是有效的
            if re.match(r'^(sh|sz|SH|SZ)\d{6}$', symbol):
                logger.info(f"Symbol {symbol} is in exchange-prefixed format")
                return True

            # 特殊情况：如果是指数代码，可能有不同格式
            if re.match(r'^(000\d{3}|399\d{3}|50\d{4}|51\d{4}|60\d{4})$', symbol):
                logger.info(f"Symbol {symbol} appears to be an index code")
                return True

            logger.warning(f"Symbol {symbol} does not match any known format")
            return False
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            # 出错时宽松处理，允许继续
            return True

    def _validate_and_format_date(self, date_str: str) -> str:
        """
        Validate and format date string.

        Args:
            date_str: Date string in various formats.

        Returns:
            Formatted date string in YYYYMMDD format.
        """
        logger.info(f"Validating and formatting date: '{date_str}' (type: {type(date_str).__name__})")

        if not date_str:
            current_date = datetime.now().strftime('%Y%m%d')
            logger.info(f"No date provided, using current date: {current_date}")
            return current_date

        # 如果已经是正确的格式，直接返回
        if re.match(r'^\d{8}$', date_str):
            # 验证日期是否有效
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                # 检查日期是否在合理范围内（例如，不是未来日期，不是太远的过去）
                now = datetime.now()
                if date_obj > now:
                    logger.warning(f"Date {date_str} is in the future. Using current date instead.")
                    return now.strftime('%Y%m%d')

                # 检查是否是太远的过去（例如，超过30年）
                if (now - date_obj).days > 30 * 365:
                    logger.warning(f"Date {date_str} is more than 30 years in the past. This may be invalid.")

                return date_str
            except ValueError:
                logger.warning(f"Date string {date_str} has correct format but is not a valid date")
                # 继续尝试其他格式

        # 尝试不同的日期格式
        formats = [
            '%Y%m%d',      # 20230101
            '%Y-%m-%d',    # 2023-01-01
            '%Y/%m/%d',    # 2023/01/01
            '%m/%d/%Y',    # 01/01/2023
            '%d/%m/%Y',    # 01/01/2023 (欧洲格式)
            '%Y.%m.%d',    # 2023.01.01
            '%d.%m.%Y',    # 01.01.2023
            '%d-%m-%Y',    # 01-01-2023
            '%Y年%m月%d日', # 2023年01月01日 (中文格式)
            '%b %d, %Y',   # Jan 01, 2023
            '%d %b %Y',    # 01 Jan 2023
            '%B %d, %Y',   # January 01, 2023
            '%d %B %Y'     # 01 January 2023
        ]

        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                formatted_date = date_obj.strftime('%Y%m%d')
                logger.debug(f"Successfully parsed date {date_str} using format {fmt} -> {formatted_date}")

                # 检查日期是否在合理范围内
                now = datetime.now()
                if date_obj > now:
                    logger.warning(f"Parsed date {formatted_date} is in the future. Using current date instead.")
                    return now.strftime('%Y%m%d')

                return formatted_date
            except ValueError:
                continue

        # 如果所有格式都失败，尝试使用pandas的日期解析
        try:
            date_obj = pd.to_datetime(date_str, errors='raise')
            formatted_date = date_obj.strftime('%Y%m%d')
            logger.info(f"Parsed date {date_str} using pandas -> {formatted_date}")

            # 检查日期是否在合理范围内
            now = datetime.now()
            if date_obj > now:
                logger.warning(f"Parsed date {formatted_date} is in the future. Using current date instead.")
                return now.strftime('%Y%m%d')

            return formatted_date
        except Exception as e:
            logger.error(f"Failed to parse date {date_str} using pandas: {e}")

        # 如果是相对日期描述，尝试解析
        if date_str.lower() == 'today' or date_str.lower() == 'now' or date_str.lower() == 'current':
            return datetime.now().strftime('%Y%m%d')
        elif date_str.lower() == 'yesterday':
            return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        elif date_str.lower() == 'last week':
            return (datetime.now() - timedelta(weeks=1)).strftime('%Y%m%d')
        elif date_str.lower() == 'last month':
            return (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        elif date_str.lower() == 'last year':
            return (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        # 使用正则表达式匹配更复杂的模式
        relative_date_patterns = {
            r'(?i)(\d+)\s*days?\s*ago': lambda m: datetime.now() - timedelta(days=int(m.group(1))),
            r'(?i)(\d+)\s*weeks?\s*ago': lambda m: datetime.now() - timedelta(weeks=int(m.group(1))),
            r'(?i)(\d+)\s*months?\s*ago': lambda m: datetime.now() - timedelta(days=30*int(m.group(1))),
            r'(?i)(\d+)\s*years?\s*ago': lambda m: datetime.now() - timedelta(days=365*int(m.group(1))),
            r'(?i)(\d{4})': lambda m: datetime(int(m.group(1)), 1, 1)  # 只有年份的情况，如"2023"
        }

        for pattern, date_func in relative_date_patterns.items():
            match = re.match(pattern, date_str)
            if match:
                try:
                    date_obj = date_func(match) if callable(date_func) else date_func()
                    formatted_date = date_obj.strftime('%Y%m%d')
                    logger.info(f"Parsed relative date {date_str} -> {formatted_date}")
                    return formatted_date
                except Exception as e:
                    logger.error(f"Error parsing relative date {date_str}: {e}")

        # 如果所有尝试都失败，使用当前日期并记录警告
        logger.warning(f"Could not parse date string: {date_str}. Using current date instead.")
        return datetime.now().strftime('%Y%m%d')

    def _compare_dates(self, date_str1: str, date_str2: str) -> int:
        """
        Compare two date strings.

        Args:
            date_str1: First date string in format YYYYMMDD.
            date_str2: Second date string in format YYYYMMDD.

        Returns:
            -1 if date1 < date2, 0 if date1 == date2, 1 if date1 > date2.
        """
        try:
            date1 = datetime.strptime(date_str1, '%Y%m%d')
            date2 = datetime.strptime(date_str2, '%Y%m%d')

            if date1 < date2:
                return -1
            elif date1 > date2:
                return 1
            else:
                return 0
        except ValueError as e:
            raise ValueError(f"Error comparing dates: {e}")

    def _is_future_date(self, date_str: str) -> bool:
        """
        Check if a date string represents a future date.

        Args:
            date_str: Date string in format YYYYMMDD.

        Returns:
            True if the date is in the future, False otherwise.
        """
        if not date_str:
            return False

        try:
            date = datetime.strptime(date_str, '%Y%m%d')
            return date > datetime.now()
        except ValueError:
            return False

    def _validate_stock_data(self, df: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> bool:
        """
        Validate stock data for completeness and correctness.

        Args:
            df: DataFrame with stock data.
            symbol: Stock symbol.
            start_date: Start date in format YYYYMMDD.
            end_date: End date in format YYYYMMDD.

        Returns:
            True if the data is valid, False otherwise.
        """
        if df.empty:
            logger.warning(f"Empty DataFrame for {symbol}")
            return False

        # 检查必要的列是否存在
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing required column '{col}' in data for {symbol}")
                return False

        # 检查数据类型
        try:
            # 确保日期列是日期类型
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])

            # 检查数值列
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    logger.warning(f"Column '{col}' is not numeric in data for {symbol}")
                    return False

            # 检查是否有无效值（NaN）
            for col in numeric_columns:
                if df[col].isna().any():
                    nan_count = df[col].isna().sum()
                    if nan_count > len(df) * 0.1:  # 如果超过10%的数据是NaN，则认为数据无效
                        logger.warning(f"Too many NaN values ({nan_count}) in column '{col}' for {symbol}")
                        return False
                    else:
                        logger.warning(f"Some NaN values ({nan_count}) in column '{col}' for {symbol}, but within acceptable range")

            # 检查数据范围
            start_date_dt = pd.to_datetime(start_date, format="%Y%m%d")
            end_date_dt = pd.to_datetime(end_date, format="%Y%m%d")

            # 计算应该有的交易日数量（粗略估计，考虑周末和节假日）
            business_days = pd.date_range(start=start_date_dt, end=end_date_dt, freq='B')
            expected_days = len(business_days)

            # 如果数据量太少（少于预期的50%），可能数据不完整
            if len(df) < expected_days * 0.5:
                logger.warning(f"Data for {symbol} may be incomplete. Got {len(df)} rows, expected around {expected_days}")
                # 但不要因此判定数据无效，因为可能是新上市的股票或者停牌等原因

            # 检查价格是否合理（不为0或者异常值）
            if (df['close'] <= 0).any() or (df['high'] <= 0).any() or (df['low'] <= 0).any() or (df['open'] <= 0).any():
                logger.warning(f"Found non-positive price values in data for {symbol}")
                return False

            # 检查最高价是否大于等于最低价
            if (df['high'] < df['low']).any():
                logger.warning(f"Found high price less than low price in data for {symbol}")
                return False

            # 检查成交量是否合理
            if (df['volume'] < 0).any():
                logger.warning(f"Found negative volume in data for {symbol}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating data for {symbol}: {e}")
            return False

    def _convert_to_period(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        Convert daily data to weekly or monthly data.

        Args:
            df: DataFrame with daily stock data.
            period: Target period, either "weekly" or "monthly".

        Returns:
            DataFrame with data converted to the specified period.
        """
        if period not in ["weekly", "monthly"]:
            logger.warning(f"Invalid period: {period}. Returning original data.")
            return df

        if df.empty:
            return df

        try:
            # 确保日期列是日期类型
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])

            # 设置日期为索引
            df = df.set_index('date')

            # 确定重采样频率
            freq = 'W-MON' if period == "weekly" else 'MS'  # 周一为一周的开始，月初为一个月的开始

            # 定义重采样规则
            agg_dict = {
                'open': 'first',     # 周期第一天的开盘价
                'high': 'max',       # 周期内的最高价
                'low': 'min',        # 周期内的最低价
                'close': 'last',     # 周期最后一天的收盘价
                'volume': 'sum'      # 周期内的成交量之和
            }

            # 添加其他可能存在的列
            for col in df.columns:
                if col not in agg_dict and col not in ['date']:
                    if col in ['turnover', 'amount']:
                        agg_dict[col] = 'sum'  # 成交额之和
                    elif col in ['pct_change', 'change', 'amplitude']:
                        # 这些列需要重新计算，不能简单地聚合
                        pass
                    else:
                        agg_dict[col] = 'last'  # 默认使用最后一个值

            # 执行重采样
            resampled = df.resample(freq).agg(agg_dict)

            # 重新计算涨跌幅和振幅
            if 'pct_change' in df.columns:
                # 计算周期内的涨跌幅（收盘价相对于上一周期收盘价的变化百分比）
                resampled['pct_change'] = resampled['close'].pct_change() * 100

            if 'change' in df.columns:
                # 计算周期内的涨跌额（收盘价相对于上一周期收盘价的变化）
                resampled['change'] = resampled['close'].diff()

            if 'amplitude' in df.columns:
                # 计算周期内的振幅（最高价与最低价之差相对于收盘价的百分比）
                resampled['amplitude'] = (resampled['high'] - resampled['low']) / resampled['close'] * 100

            # 重置索引，将日期列恢复为普通列
            resampled = resampled.reset_index()

            # 将日期格式化为字符串
            resampled['date'] = resampled['date'].dt.strftime('%Y-%m-%d')

            # 删除包含NaN的行（通常是第一行，因为计算涨跌幅需要前一个周期的数据）
            resampled = resampled.dropna(subset=['close'])

            logger.info(f"Converted daily data to {period} data. Original rows: {len(df)}, new rows: {len(resampled)}")

            return resampled

        except Exception as e:
            logger.error(f"Error converting data to {period}: {e}")
            # 返回原始数据
            return df

    def _generate_mock_stock_data(self, symbol: str, start_date: str, end_date: str, adjust: str = "", period: str = "daily") -> pd.DataFrame:
        """
        Generate mock stock data for testing purposes.

        Args:
            symbol: Stock symbol.
            start_date: Start date in format YYYYMMDD.
            end_date: End date in format YYYYMMDD.
            adjust: Price adjustment method. Options are:
                   "" (empty string): No adjustment
                   "qfq": Forward adjustment
                   "hfq": Backward adjustment
            period: Data frequency. Options are "daily", "weekly", "monthly".

        Returns:
            DataFrame with mock stock data.
        """
        logger.info(f"Generating mock data for {symbol} from {start_date} to {end_date} with adjust={adjust}, period={period}")

        try:
            # Parse dates
            start = datetime.strptime(start_date, '%Y%m%d')
            end = datetime.strptime(end_date, '%Y%m%d')

            # Determine frequency based on period
            if period == "weekly":
                freq = 'W-MON'  # Weekly data on Mondays
            elif period == "monthly":
                freq = 'MS'     # Monthly data on the first day of each month
            else:  # daily
                freq = 'B'      # Business days (excludes weekends)

            # Generate date range
            date_range = pd.date_range(start=start, end=end, freq=freq)

            # If no dates in range, return empty DataFrame with correct columns
            if len(date_range) == 0:
                logger.warning(f"No dates in range from {start_date} to {end_date} with period={period}")
                return pd.DataFrame(columns=[
                    'date', 'open', 'high', 'low', 'close', 'volume',
                    'turnover', 'amplitude', 'pct_change', 'change'
                ])

            # Generate random data
            import numpy as np

            # Use symbol to determine base price (more realistic)
            if symbol.isdigit():
                # For Chinese stocks (typically 6-digit codes)
                if len(symbol) == 6:
                    # Use first digit to determine price range
                    first_digit = int(symbol[0])
                    if first_digit in [0, 3]:  # 深圳股票
                        base_price = np.random.uniform(5.0, 30.0)
                    elif first_digit == 6:  # 上海股票
                        base_price = np.random.uniform(5.0, 50.0)
                    elif first_digit in [8, 4]:  # 北交所、新三板
                        base_price = np.random.uniform(10.0, 100.0)
                    else:
                        base_price = np.random.uniform(10.0, 50.0)
                else:
                    base_price = np.random.uniform(10.0, 100.0)
            else:
                base_price = np.random.uniform(50.0, 200.0)  # For non-numeric symbols (e.g., US stocks)

            # Adjust volatility based on period
            if period == "daily":
                volatility = 0.015  # 1.5% daily volatility
            elif period == "weekly":
                volatility = 0.03   # 3% weekly volatility
            else:  # monthly
                volatility = 0.06   # 6% monthly volatility

            # Generate random price movements with trend
            np.random.seed(int(hash(symbol)) % 2**32)  # Use hash of symbol as seed for reproducibility

            # Add a slight trend bias (50% chance of upward trend, 50% chance of downward trend)
            trend_bias = np.random.choice([-0.0005, 0.0005])

            # Generate returns with trend bias
            returns = np.random.normal(trend_bias, volatility, len(date_range))

            # Ensure no extreme returns
            returns = np.clip(returns, -0.1, 0.1)

            # Calculate cumulative returns
            price_movements = np.cumprod(1 + returns)

            # Calculate prices
            closes = base_price * price_movements

            # Generate realistic open, high, low prices
            opens = closes * np.random.uniform(0.985, 1.015, len(date_range))

            # Ensure high is always the highest price
            highs = np.maximum(opens, closes) * np.random.uniform(1.005, 1.02, len(date_range))

            # Ensure low is always the lowest price
            lows = np.minimum(opens, closes) * np.random.uniform(0.98, 0.995, len(date_range))

            # Generate volumes based on price (higher prices tend to have lower volumes)
            avg_volume = 10000000 / (base_price / 10)  # Adjust volume based on price
            volume_volatility = 0.5  # 50% volume volatility

            # Generate log-normal volumes (more realistic)
            log_volumes = np.random.normal(np.log(avg_volume), volume_volatility, len(date_range))
            volumes = np.exp(log_volumes).astype(int)

            # Apply price adjustments if requested
            if adjust == "qfq":  # Forward adjustment (前复权)
                # Simulate multiple corporate actions
                num_actions = max(1, len(date_range) // 60)  # Approximately one action every 3 months

                for _ in range(num_actions):
                    # Random point for corporate action
                    action_point = np.random.randint(10, len(date_range) - 10)

                    # Random adjustment factor (dividend or split)
                    adjustment_factor = np.random.choice([0.95, 0.9, 0.8, 0.5])  # Various adjustment sizes

                    # Apply forward adjustment (affects prices before the action)
                    for i in range(action_point):
                        opens[i] *= adjustment_factor
                        highs[i] *= adjustment_factor
                        lows[i] *= adjustment_factor
                        closes[i] *= adjustment_factor

            elif adjust == "hfq":  # Backward adjustment (后复权)
                # Simulate multiple corporate actions
                num_actions = max(1, len(date_range) // 60)  # Approximately one action every 3 months

                for _ in range(num_actions):
                    # Random point for corporate action
                    action_point = np.random.randint(10, len(date_range) - 10)

                    # Random adjustment factor (dividend or split)
                    adjustment_factor = np.random.choice([1.05, 1.1, 1.2, 2.0])  # Various adjustment sizes

                    # Apply backward adjustment (affects prices after the action)
                    for i in range(action_point, len(date_range)):
                        opens[i] *= adjustment_factor
                        highs[i] *= adjustment_factor
                        lows[i] *= adjustment_factor
                        closes[i] *= adjustment_factor

            # Calculate derived fields
            turnovers = volumes * closes
            amplitudes = (highs - lows) / closes * 100

            # Calculate actual price changes and percentages
            changes = np.zeros_like(closes)
            pct_changes = np.zeros_like(closes)

            # First day has no change
            for i in range(1, len(date_range)):
                changes[i] = closes[i] - closes[i-1]
                pct_changes[i] = (changes[i] / closes[i-1]) * 100

            # Create DataFrame
            df = pd.DataFrame({
                'date': date_range.strftime('%Y-%m-%d'),
                'open': np.round(opens, 2),  # Round to 2 decimal places
                'high': np.round(highs, 2),
                'low': np.round(lows, 2),
                'close': np.round(closes, 2),
                'volume': volumes,
                'turnover': np.round(turnovers, 2),
                'amplitude': np.round(amplitudes, 2),
                'pct_change': np.round(pct_changes, 2),
                'change': np.round(changes, 2)
            })

            logger.info(f"Successfully generated mock data with {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return minimal mock data with correct date range
            try:
                # Try to create a minimal dataset with the correct date range
                if start_date and end_date:
                    start = datetime.strptime(start_date, '%Y%m%d')
                    end = datetime.strptime(end_date, '%Y%m%d')

                    # Use business day frequency for minimal dataset
                    date_range = pd.date_range(start=start, end=end, freq='B')

                    if len(date_range) > 0:
                        # Create a simple dataset with constant values
                        return pd.DataFrame({
                            'date': date_range.strftime('%Y-%m-%d'),
                            'open': [100.0] * len(date_range),
                            'high': [105.0] * len(date_range),
                            'low': [95.0] * len(date_range),
                            'close': [102.0] * len(date_range),
                            'volume': [5000000] * len(date_range),
                            'turnover': [510000000.0] * len(date_range),
                            'amplitude': [10.0] * len(date_range),
                            'pct_change': [0.0] * len(date_range),
                            'change': [0.0] * len(date_range)
                        })
            except Exception as inner_e:
                logger.error(f"Error creating minimal mock data: {inner_e}")

            # If all else fails, return a single row of data
            return pd.DataFrame({
                'date': [datetime.now().strftime('%Y-%m-%d')],
                'open': [100.0],
                'high': [105.0],
                'low': [95.0],
                'close': [102.0],
                'volume': [5000000],
                'turnover': [510000000.0],
                'amplitude': [10.0],
                'pct_change': [0.0],
                'change': [0.0]
            })

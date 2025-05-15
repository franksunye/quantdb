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

from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
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

            return result
        except Exception as e:
            logger.error(f"Error calling AKShare function {func.__name__}: {e}")
            logger.error(f"Function arguments: args={args}, kwargs={kwargs}")
            # 记录更详细的错误信息
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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

        # Validate symbol format
        if not self._validate_symbol(symbol):
            logger.error(f"Invalid symbol format: {symbol}")
            raise ValueError(f"Invalid symbol format: {symbol}. Symbol should be a 6-digit number.")

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

        # 标准化股票代码 - 移除市场前缀和后缀，只保留数字部分
        # 因为 stock_zh_a_hist 函数需要的是不带前缀的纯数字代码
        original_symbol = symbol

        # 移除可能的后缀
        if "." in symbol:
            symbol = symbol.split(".")[0]

        # 移除可能的市场前缀
        if symbol.startswith("sh") or symbol.startswith("sz") or symbol.startswith("SH") or symbol.startswith("SZ"):
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
                return df
            else:
                logger.warning(f"stock_zh_a_hist returned empty data for {symbol}")
        except Exception as e:
            logger.error(f"Error getting data using stock_zh_a_hist for {symbol}: {e}")

        # 如果 stock_zh_a_hist 失败，尝试使用 stock_zh_a_hist_tx 函数（腾讯数据源）
        try:
            # 为腾讯数据源准备带前缀的代码
            tx_symbol = original_symbol

            # 如果没有市场前缀，添加前缀
            if not (tx_symbol.startswith("sh") or tx_symbol.startswith("sz") or
                    tx_symbol.startswith("SH") or tx_symbol.startswith("SZ")):
                # 根据股票代码判断市场
                if tx_symbol.startswith("6"):
                    tx_symbol = f"sh{tx_symbol}"
                else:
                    tx_symbol = f"sz{tx_symbol}"

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
                    return filtered_df
                else:
                    logger.warning(f"No data found for {tx_symbol} in date range {start_date} to {end_date}")
            else:
                logger.warning(f"stock_zh_a_hist_tx returned empty data for {tx_symbol}")
        except Exception as e:
            logger.error(f"Error getting data using stock_zh_a_hist_tx for {tx_symbol}: {e}")

        # 如果是指数，尝试使用 stock_zh_index_daily 函数
        try:
            # 检查是否可能是指数
            if symbol.endswith("000001") or symbol.endswith("399001") or symbol.endswith("000300"):
                # 为指数数据源准备带前缀的代码
                index_symbol = original_symbol

                # 如果没有市场前缀，添加前缀
                if not (index_symbol.startswith("sh") or index_symbol.startswith("sz") or
                        index_symbol.startswith("SH") or index_symbol.startswith("SZ")):
                    # 根据指数代码判断市场
                    if index_symbol.startswith("0") or index_symbol.startswith("9"):
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
                        return filtered_df
                    else:
                        logger.warning(f"No data found for index {index_symbol} in date range {start_date} to {end_date}")
                else:
                    logger.warning(f"stock_zh_index_daily returned empty data for {index_symbol}")
        except Exception as e:
            logger.error(f"Error getting data using stock_zh_index_daily for index: {e}")

        # 如果所有数据源都失败，并且允许使用模拟数据
        if use_mock_data:
            logger.warning(f"All data sources failed for {symbol}. Using mock data as requested.")
            return self._generate_mock_stock_data(symbol, start_date, end_date, adjust)

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
        if not date_str:
            return datetime.now().strftime('%Y%m%d')

        # 如果已经是正确的格式，直接返回
        if re.match(r'^\d{8}$', date_str):
            # 验证日期是否有效
            try:
                datetime.strptime(date_str, '%Y%m%d')
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
                return formatted_date
            except ValueError:
                continue

        # 如果所有格式都失败，尝试使用pandas的日期解析
        try:
            date_obj = pd.to_datetime(date_str, errors='raise')
            formatted_date = date_obj.strftime('%Y%m%d')
            logger.info(f"Parsed date {date_str} using pandas -> {formatted_date}")
            return formatted_date
        except Exception as e:
            logger.error(f"Failed to parse date {date_str} using pandas: {e}")

        # 如果是相对日期描述，尝试解析
        relative_date_patterns = {
            r'(?i)today|now|current': lambda: datetime.now(),
            r'(?i)yesterday': lambda: datetime.now() - timedelta(days=1),
            r'(?i)(\d+)\s*days?\s*ago': lambda m: datetime.now() - timedelta(days=int(m.group(1))),
            r'(?i)(\d+)\s*weeks?\s*ago': lambda m: datetime.now() - timedelta(weeks=int(m.group(1))),
            r'(?i)(\d+)\s*months?\s*ago': lambda m: datetime.now() - timedelta(days=30*int(m.group(1))),
            r'(?i)(\d+)\s*years?\s*ago': lambda m: datetime.now() - timedelta(days=365*int(m.group(1))),
            r'(?i)last\s*week': lambda: datetime.now() - timedelta(weeks=1),
            r'(?i)last\s*month': lambda: datetime.now() - timedelta(days=30),
            r'(?i)last\s*year': lambda: datetime.now() - timedelta(days=365)
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

    def _generate_mock_stock_data(self, symbol: str, start_date: str, end_date: str, adjust: str = "") -> pd.DataFrame:
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

        Returns:
            DataFrame with mock stock data.
        """
        logger.info(f"Generating mock data for {symbol} from {start_date} to {end_date} with adjust={adjust}")

        try:
            # Parse dates
            start = datetime.strptime(start_date, '%Y%m%d')
            end = datetime.strptime(end_date, '%Y%m%d')

            # Generate date range
            date_range = pd.date_range(start=start, end=end, freq='D')

            # Generate random data
            import numpy as np
            base_price = 100.0  # Base price
            volatility = 0.02   # Daily volatility

            # Generate random price movements
            np.random.seed(int(symbol) if symbol.isdigit() else 0)  # Use symbol as seed for reproducibility
            returns = np.random.normal(0, volatility, len(date_range))
            price_movements = np.cumprod(1 + returns)

            # Calculate prices
            closes = base_price * price_movements
            opens = closes * np.random.uniform(0.98, 1.02, len(date_range))
            highs = np.maximum(opens, closes) * np.random.uniform(1.0, 1.03, len(date_range))
            lows = np.minimum(opens, closes) * np.random.uniform(0.97, 1.0, len(date_range))
            volumes = np.random.randint(1000000, 10000000, len(date_range))

            # Apply price adjustments if requested
            if adjust == "qfq":  # Forward adjustment (前复权)
                # Simulate a stock split or dividend at a random point
                split_point = len(date_range) // 2
                adjustment_factor = 0.9  # 10% adjustment

                # Apply forward adjustment (affects prices before the split)
                for i in range(split_point):
                    opens[i] *= adjustment_factor
                    highs[i] *= adjustment_factor
                    lows[i] *= adjustment_factor
                    closes[i] *= adjustment_factor

            elif adjust == "hfq":  # Backward adjustment (后复权)
                # Simulate a stock split or dividend at a random point
                split_point = len(date_range) // 2
                adjustment_factor = 1.1  # 10% adjustment

                # Apply backward adjustment (affects prices after the split)
                for i in range(split_point, len(date_range)):
                    opens[i] *= adjustment_factor
                    highs[i] *= adjustment_factor
                    lows[i] *= adjustment_factor
                    closes[i] *= adjustment_factor

            # Create DataFrame
            df = pd.DataFrame({
                'date': date_range.strftime('%Y-%m-%d'),
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes,
                'turnover': volumes * closes,
                'amplitude': (highs - lows) / closes * 100,
                'pct_change': returns * 100,
                'change': returns * closes
            })

            return df

        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            # Return minimal mock data
            return pd.DataFrame({
                'date': [datetime.now().strftime('%Y-%m-%d')],
                'open': [100.0],
                'high': [105.0],
                'low': [95.0],
                'close': [102.0],
                'volume': [5000000],
                'turnover': [510000000.0],
                'amplitude': [10.0],
                'pct_change': [2.0],
                'change': [2.0]
            })

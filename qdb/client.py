"""
QDB Lightweight Client - True Frontend Layer

This module provides a lightweight wrapper around core services,
following the architecture principle: "核心功能都在core里面，qdb只是前端的一个调用"

Key principles:
- NO complex business logic in qdb
- NO service initialization logic in qdb  
- NO parameter processing logic in qdb
- ONLY simple delegation to core services
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .exceptions import QDBError

# Lazy import of core services to avoid heavy dependencies
def _get_service_manager():
    """Lazy import of service manager to avoid loading heavy dependencies at import time."""
    try:
        from core.services import get_service_manager
        return get_service_manager()
    except ImportError as e:
        raise QDBError(f"Failed to import core services: {e}. Please install required dependencies.")


class LightweightQDBClient:
    """
    Lightweight QDB client that delegates ALL functionality to core services.
    
    This client contains ZERO business logic - it's purely a thin wrapper
    that calls the core ServiceManager. All complex logic is in core/.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize lightweight client.

        Args:
            cache_dir: Cache directory path (passed to ServiceManager)
        """
        # Store cache_dir for lazy initialization
        self._cache_dir = cache_dir
        self._service_manager = None

    def _get_service_manager(self):
        """Get service manager with lazy initialization."""
        if self._service_manager is None:
            service_manager_factory = _get_service_manager()
            if self._cache_dir:
                # Reset and create with specific cache_dir
                from core.services import reset_service_manager, get_service_manager
                reset_service_manager()
                self._service_manager = get_service_manager(cache_dir=self._cache_dir)
            else:
                self._service_manager = service_manager_factory
        return self._service_manager

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        adjust: str = "",
    ):
        """Get historical stock data with intelligent caching.

        Retrieves historical stock price data for Chinese A-shares with automatic
        caching to improve performance. Data is fetched from AKShare and cached
        locally using SQLite. This is a lightweight wrapper that delegates all
        functionality to core services.

        Args:
            symbol (str): Stock symbol in 6-digit format. Supports:
                - Shanghai Stock Exchange: 600000-699999
                - Shenzhen Stock Exchange: 000000-399999
                - ChiNext: 300000-399999
                - Examples: "000001", "600000", "300001"
            start_date (str, optional): Start date in YYYYMMDD format.
                Must be a valid trading date. Example: "20240101"
            end_date (str, optional): End date in YYYYMMDD format.
                Must be >= start_date. Example: "20240201"
            days (int, optional): Number of recent trading days to fetch.
                Range: 1-1000. Mutually exclusive with start_date/end_date.
            adjust (str, optional): Price adjustment type. Options:
                - "": No adjustment (default)
                - "qfq": Forward adjustment (recommended for returns analysis)
                - "hfq": Backward adjustment

        Returns:
            pd.DataFrame: Historical stock data with columns:
                - date (datetime): Trading date
                - open (float): Opening price in CNY
                - high (float): Highest price in CNY
                - low (float): Lowest price in CNY
                - close (float): Closing price in CNY
                - volume (int): Trading volume (shares)
                - amount (float): Trading amount in CNY

        Raises:
            QDBError: If core service fails or data cannot be retrieved.
                Common causes:
                - Invalid symbol format
                - Invalid date parameters
                - Network connectivity issues
                - Data source unavailable

        Examples:
            Get last 30 days of data:
            >>> client = LightweightQDBClient()
            >>> df = client.get_stock_data("000001", days=30)
            >>> print(f"Retrieved {len(df)} trading days")

            Get data for specific date range:
            >>> df = client.get_stock_data(
            ...     "600000",
            ...     start_date="20240101",
            ...     end_date="20240201"
            ... )

            Get forward-adjusted data for analysis:
            >>> df = client.get_stock_data("000001", days=100, adjust="qfq")
            >>> returns = df['close'].pct_change()

        Note:
            - Data is automatically cached for improved performance (90%+ speedup)
            - Only trading days are included in the results
            - Cache is updated automatically for recent data
            - Historical data (>1 day old) is cached permanently
            - Uses lazy initialization of core services
        """
        try:
            stock_service = self._get_service_manager().get_stock_data_service()

            # Let core service handle ALL parameter processing and business logic
            if days is not None:
                return stock_service.get_stock_data_by_days(symbol, days, adjust)
            else:
                return stock_service.get_stock_data(symbol, start_date, end_date, adjust)

        except Exception as e:
            raise QDBError(f"Failed to get stock data: {str(e)}")
    
    def get_multiple_stocks(
        self, symbols: List[str], days: int = 30, **kwargs
    ):
        """Get historical data for multiple stocks efficiently.

        Retrieves historical stock data for multiple symbols with optimized
        batch processing and intelligent caching. This method is more efficient
        than calling get_stock_data() multiple times.

        Args:
            symbols (List[str]): List of stock symbols in 6-digit format.
                Each symbol should follow the same format as get_stock_data().
                Example: ["000001", "600000", "300001"]
            days (int, optional): Number of recent trading days to fetch.
                Range: 1-1000. Default: 30.
            **kwargs: Additional parameters passed to core service.
                May include adjust, force_refresh, etc.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping symbols to DataFrames.
                Each DataFrame has the same structure as get_stock_data().
                Failed symbols may return empty DataFrames.

        Raises:
            QDBError: If core service fails or batch processing encounters errors.

        Examples:
            Get data for multiple stocks:
            >>> client = LightweightQDBClient()
            >>> symbols = ["000001", "600000", "300001"]
            >>> data = client.get_multiple_stocks(symbols, days=30)
            >>> for symbol, df in data.items():
            ...     print(f"{symbol}: {len(df)} days")

            With price adjustment:
            >>> data = client.get_multiple_stocks(
            ...     ["000001", "600000"],
            ...     days=60,
            ...     adjust="qfq"
            ... )

        Note:
            - Uses batch processing for improved performance
            - Individual symbol failures don't affect other symbols
            - Results are cached independently for each symbol
        """
        try:
            stock_service = self._get_service_manager().get_stock_data_service()
            return stock_service.get_multiple_stocks(symbols, days, **kwargs)
        except Exception as e:
            raise QDBError(f"Failed to get multiple stocks data: {str(e)}")

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive asset information for a stock symbol.

        Retrieves detailed information about a stock including company name,
        industry classification, market capitalization, and other fundamental
        data. This information is cached for performance.

        Args:
            symbol (str): Stock symbol in 6-digit format.
                Same format as get_stock_data(). Example: "000001"

        Returns:
            Dict[str, Any]: Asset information dictionary containing:
                - name (str): Company name in Chinese
                - industry (str): Industry classification
                - market (str): Market exchange (SHSE/SZSE)
                - market_cap (float): Market capitalization in CNY
                - pe_ratio (float): Price-to-earnings ratio
                - pb_ratio (float): Price-to-book ratio
                - Additional fields may vary by data source

        Raises:
            QDBError: If asset information cannot be retrieved.
                Common causes:
                - Invalid symbol format
                - Symbol not found in database
                - Data source unavailable

        Examples:
            Get basic asset information:
            >>> client = LightweightQDBClient()
            >>> info = client.get_asset_info("000001")
            >>> print(f"Company: {info['name']}")
            >>> print(f"Industry: {info['industry']}")

            Check market capitalization:
            >>> info = client.get_asset_info("600000")
            >>> if 'market_cap' in info:
            ...     print(f"Market Cap: {info['market_cap']:,.0f} CNY")

        Note:
            - Asset information is cached for 24 hours
            - Some fields may be None if data is unavailable
            - Information is updated during trading hours
        """
        try:
            asset_service = self._get_service_manager().get_asset_info_service()
            return asset_service.get_asset_info(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get asset info: {str(e)}")

    def get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time market data for a stock symbol.

        Retrieves current market data including latest price, bid/ask spreads,
        trading volume, and market status. Data is refreshed during trading
        hours and cached for short periods to balance accuracy and performance.

        Args:
            symbol (str): Stock symbol in 6-digit format.
                Same format as get_stock_data(). Example: "000001"

        Returns:
            Dict[str, Any]: Real-time market data containing:
                - current_price (float): Latest trading price in CNY
                - change (float): Price change from previous close
                - change_percent (float): Percentage change from previous close
                - volume (int): Current day trading volume
                - amount (float): Current day trading amount in CNY
                - bid_price (float): Best bid price
                - ask_price (float): Best ask price
                - high (float): Day's highest price
                - low (float): Day's lowest price
                - open (float): Day's opening price
                - timestamp (datetime): Data timestamp
                - market_status (str): "open", "closed", "pre_market", "after_hours"

        Raises:
            QDBError: If real-time data cannot be retrieved.
                Common causes:
                - Invalid symbol format
                - Market closed and no cached data
                - Data source unavailable
                - Network connectivity issues

        Examples:
            Get current price and change:
            >>> client = LightweightQDBClient()
            >>> data = client.get_realtime_data("000001")
            >>> print(f"Price: ¥{data['current_price']:.2f}")
            >>> print(f"Change: {data['change_percent']:.2f}%")

            Check market status:
            >>> data = client.get_realtime_data("600000")
            >>> if data['market_status'] == 'open':
            ...     print("Market is currently open")

            Monitor bid-ask spread:
            >>> data = client.get_realtime_data("300001")
            >>> spread = data['ask_price'] - data['bid_price']
            >>> print(f"Bid-Ask Spread: ¥{spread:.3f}")

        Note:
            - Data is cached for 1-5 minutes during trading hours
            - Outside trading hours, returns last available data
            - Some fields may be None if market is closed
            - Timestamp indicates when data was last updated
        """
        try:
            realtime_service = self._get_service_manager().get_realtime_data_service()
            return realtime_service.get_realtime_data(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get realtime data: {str(e)}")
    
    def get_realtime_data_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get real-time market data for multiple stocks efficiently.

        Retrieves current market data for multiple symbols with optimized
        batch processing. This method is more efficient than calling
        get_realtime_data() multiple times.

        Args:
            symbols (List[str]): List of stock symbols in 6-digit format.
                Each symbol should follow the same format as get_realtime_data().
                Example: ["000001", "600000", "300001"]

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping symbols to real-time data.
                Each value has the same structure as get_realtime_data().
                Failed symbols may return empty dictionaries or error indicators.

        Raises:
            QDBError: If batch real-time data retrieval fails.

        Examples:
            Get real-time data for multiple stocks:
            >>> client = LightweightQDBClient()
            >>> symbols = ["000001", "600000", "300001"]
            >>> data = client.get_realtime_data_batch(symbols)
            >>> for symbol, info in data.items():
            ...     if 'current_price' in info:
            ...         print(f"{symbol}: ¥{info['current_price']:.2f}")

            Monitor portfolio performance:
            >>> portfolio = ["000001", "600000", "300001"]
            >>> data = client.get_realtime_data_batch(portfolio)
            >>> total_change = sum(
            ...     info.get('change_percent', 0)
            ...     for info in data.values()
            ... ) / len(data)
            >>> print(f"Average change: {total_change:.2f}%")

        Note:
            - Uses batch processing for improved performance
            - Individual symbol failures don't affect other symbols
            - Data freshness same as get_realtime_data()
            - Results may have different timestamps per symbol
        """
        try:
            realtime_service = self._get_service_manager().get_realtime_data_service()
            return realtime_service.get_realtime_data_batch(symbols)
        except Exception as e:
            raise QDBError(f"Failed to get batch realtime data: {str(e)}")

    def get_stock_list(self, market: str = "all"):
        """Get comprehensive list of available stocks with filtering options.

        Retrieves a complete list of stocks available for trading with optional
        market filtering. The list includes basic information for each stock
        and is cached for performance.

        Args:
            market (str, optional): Market filter. Options:
                - "all": All available markets (default)
                - "SHSE": Shanghai Stock Exchange only
                - "SZSE": Shenzhen Stock Exchange only
                - "ChiNext": ChiNext board only
                - "STAR": STAR Market (科创板) only

        Returns:
            pd.DataFrame: Stock list with columns:
                - symbol (str): 6-digit stock symbol
                - name (str): Company name in Chinese
                - market (str): Exchange market
                - industry (str): Industry classification
                - list_date (datetime): IPO/listing date
                - status (str): Trading status ("active", "suspended", etc.)

        Raises:
            QDBError: If stock list cannot be retrieved.
                Common causes:
                - Invalid market parameter
                - Data source unavailable
                - Network connectivity issues

        Examples:
            Get all available stocks:
            >>> client = LightweightQDBClient()
            >>> stocks = client.get_stock_list()
            >>> print(f"Total stocks: {len(stocks)}")

            Filter by market:
            >>> shse_stocks = client.get_stock_list("SHSE")
            >>> szse_stocks = client.get_stock_list("SZSE")
            >>> print(f"SHSE: {len(shse_stocks)}, SZSE: {len(szse_stocks)}")

            Find stocks by industry:
            >>> stocks = client.get_stock_list()
            >>> tech_stocks = stocks[stocks['industry'].str.contains('科技')]
            >>> print(f"Tech stocks: {len(tech_stocks)}")

        Note:
            - Stock list is cached for 24 hours
            - Only actively trading stocks are included by default
            - List is updated daily after market close
            - Suspended stocks may be included with status indicator
        """
        try:
            # Use stock service for stock list functionality
            stock_service = self._get_service_manager().get_stock_data_service()
            return stock_service.get_stock_list(market)
        except Exception as e:
            raise QDBError(f"Failed to get stock list: {str(e)}")

    def get_index_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ):
        """Get historical market index data with intelligent caching.

        Retrieves historical data for market indices including Shanghai Composite,
        Shenzhen Component, ChiNext, and other major indices. Data is cached
        for improved performance.

        Args:
            symbol (str): Index symbol. Common indices:
                - "000001": Shanghai Composite Index
                - "399001": Shenzhen Component Index
                - "399006": ChiNext Index
                - "000300": CSI 300 Index
                - "000905": CSI 500 Index
                - "000016": SSE 50 Index
            start_date (str, optional): Start date in YYYYMMDD format.
                Must be a valid trading date. Example: "20240101"
            end_date (str, optional): End date in YYYYMMDD format.
                Must be >= start_date. Example: "20240201"
            days (int, optional): Number of recent trading days to fetch.
                Range: 1-1000. Mutually exclusive with start_date/end_date.

        Returns:
            pd.DataFrame: Historical index data with columns:
                - date (datetime): Trading date
                - open (float): Opening value
                - high (float): Highest value
                - low (float): Lowest value
                - close (float): Closing value
                - volume (int): Trading volume (if available)
                - amount (float): Trading amount (if available)

        Raises:
            QDBError: If index data cannot be retrieved.
                Common causes:
                - Invalid index symbol
                - Invalid date parameters
                - Data source unavailable

        Examples:
            Get Shanghai Composite last 30 days:
            >>> client = LightweightQDBClient()
            >>> df = client.get_index_data("000001", days=30)
            >>> print(f"Index range: {df['low'].min():.2f} - {df['high'].max():.2f}")

            Get CSI 300 for specific period:
            >>> df = client.get_index_data(
            ...     "000300",
            ...     start_date="20240101",
            ...     end_date="20240201"
            ... )

            Compare multiple indices:
            >>> sh_comp = client.get_index_data("000001", days=60)
            >>> sz_comp = client.get_index_data("399001", days=60)
            >>> sh_return = (sh_comp.iloc[-1]['close'] / sh_comp.iloc[0]['close'] - 1) * 100
            >>> sz_return = (sz_comp.iloc[-1]['close'] / sz_comp.iloc[0]['close'] - 1) * 100

        Note:
            - Index data is cached for improved performance
            - Only trading days are included in results
            - Volume/amount may be None for some indices
            - Data is updated after market close
        """
        try:
            index_service = self._get_service_manager().get_index_data_service()
            if days is not None:
                return index_service.get_index_data_by_days(symbol, days)
            else:
                return index_service.get_index_data(symbol, start_date, end_date)
        except Exception as e:
            raise QDBError(f"Failed to get index data: {str(e)}")

    def get_index_realtime(self, symbol: str) -> Dict[str, Any]:
        """Get real-time market index data.

        Retrieves current market index values including latest level, changes,
        and market statistics. Data is refreshed during trading hours.

        Args:
            symbol (str): Index symbol. Same format as get_index_data().
                Example: "000001" for Shanghai Composite

        Returns:
            Dict[str, Any]: Real-time index data containing:
                - current_value (float): Latest index value
                - change (float): Change from previous close
                - change_percent (float): Percentage change
                - high (float): Day's highest value
                - low (float): Day's lowest value
                - open (float): Day's opening value
                - volume (int): Total market volume (if available)
                - amount (float): Total market amount (if available)
                - timestamp (datetime): Data timestamp
                - market_status (str): Market status

        Raises:
            QDBError: If real-time index data cannot be retrieved.

        Examples:
            Monitor Shanghai Composite:
            >>> client = LightweightQDBClient()
            >>> data = client.get_index_realtime("000001")
            >>> print(f"Shanghai Composite: {data['current_value']:.2f}")
            >>> print(f"Change: {data['change_percent']:.2f}%")

            Check market sentiment:
            >>> indices = ["000001", "399001", "399006"]  # SH, SZ, ChiNext
            >>> for idx in indices:
            ...     data = client.get_index_realtime(idx)
            ...     print(f"{idx}: {data['change_percent']:.2f}%")

        Note:
            - Data cached for 1-5 minutes during trading hours
            - Outside trading hours, returns last available data
            - Market status indicates current trading state
        """
        try:
            index_service = self._get_service_manager().get_index_data_service()
            return index_service.get_realtime_index_data(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get realtime index data: {str(e)}")

    def get_index_list(self):
        """Get comprehensive list of available market indices.

        Retrieves a complete list of market indices available for querying,
        including major market indices, sector indices, and thematic indices.

        Returns:
            pd.DataFrame: Index list with columns:
                - symbol (str): Index symbol code
                - name (str): Index name in Chinese
                - name_en (str): Index name in English (if available)
                - category (str): Index category ("market", "sector", "thematic")
                - base_date (datetime): Base date for index calculation
                - base_value (float): Base value (usually 100 or 1000)
                - description (str): Index description

        Raises:
            QDBError: If index list cannot be retrieved.

        Examples:
            Get all available indices:
            >>> client = LightweightQDBClient()
            >>> indices = client.get_index_list()
            >>> print(f"Total indices: {len(indices)}")

            Find major market indices:
            >>> indices = client.get_index_list()
            >>> major_indices = indices[indices['category'] == 'market']
            >>> print(major_indices[['symbol', 'name']])

            Search for specific indices:
            >>> indices = client.get_index_list()
            >>> csi_indices = indices[indices['name'].str.contains('中证')]
            >>> print(f"CSI indices: {len(csi_indices)}")

        Note:
            - Index list is cached for 24 hours
            - Includes both active and historical indices
            - Category classification helps filter by type
            - Some fields may be None for certain indices
        """
        try:
            index_service = self._get_service_manager().get_index_data_service()
            return index_service.get_index_list()
        except Exception as e:
            raise QDBError(f"Failed to get index list: {str(e)}")

    def get_financial_summary(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive financial summary for a stock.

        Retrieves key financial metrics and ratios from the most recent
        quarterly and annual reports, providing a comprehensive overview
        of the company's financial health.

        Args:
            symbol (str): Stock symbol in 6-digit format.
                Same format as get_stock_data(). Example: "000001"

        Returns:
            Dict[str, Any]: Financial summary containing:
                - revenue (float): Total revenue (latest quarter, annualized)
                - net_income (float): Net income (latest quarter, annualized)
                - total_assets (float): Total assets
                - total_liabilities (float): Total liabilities
                - shareholders_equity (float): Shareholders' equity
                - operating_cash_flow (float): Operating cash flow
                - free_cash_flow (float): Free cash flow
                - debt_to_equity (float): Debt-to-equity ratio
                - current_ratio (float): Current ratio
                - quick_ratio (float): Quick ratio
                - roe (float): Return on equity (%)
                - roa (float): Return on assets (%)
                - gross_margin (float): Gross profit margin (%)
                - net_margin (float): Net profit margin (%)
                - report_date (datetime): Latest report date
                - currency (str): Currency unit (usually "CNY")

        Raises:
            QDBError: If financial summary cannot be retrieved.
                Common causes:
                - Invalid symbol format
                - No financial data available
                - Data source unavailable

        Examples:
            Get basic financial metrics:
            >>> client = LightweightQDBClient()
            >>> summary = client.get_financial_summary("000001")
            >>> print(f"Revenue: ¥{summary['revenue']:,.0f}")
            >>> print(f"Net Income: ¥{summary['net_income']:,.0f}")
            >>> print(f"ROE: {summary['roe']:.2f}%")

            Compare profitability:
            >>> summary = client.get_financial_summary("600000")
            >>> print(f"Gross Margin: {summary['gross_margin']:.2f}%")
            >>> print(f"Net Margin: {summary['net_margin']:.2f}%")

            Check financial health:
            >>> summary = client.get_financial_summary("300001")
            >>> print(f"Debt/Equity: {summary['debt_to_equity']:.2f}")
            >>> print(f"Current Ratio: {summary['current_ratio']:.2f}")

        Note:
            - Data is from the most recent quarterly report
            - Some metrics are annualized for comparability
            - Financial data is cached for 24 hours
            - Report date indicates data freshness
            - All monetary values are in CNY unless specified
        """
        try:
            financial_service = self._get_service_manager().get_financial_data_service()
            return financial_service.get_financial_summary(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get financial summary: {str(e)}")

    def get_financial_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get detailed financial indicators and ratios for comprehensive analysis.

        Retrieves an extensive set of financial indicators covering profitability,
        liquidity, efficiency, leverage, and growth metrics. This provides
        deeper analysis capabilities beyond the basic financial summary.

        Args:
            symbol (str): Stock symbol in 6-digit format.
                Same format as get_stock_data(). Example: "000001"

        Returns:
            Dict[str, Any]: Comprehensive financial indicators containing:
                Profitability Ratios:
                - gross_profit_margin (float): Gross profit margin (%)
                - operating_profit_margin (float): Operating profit margin (%)
                - net_profit_margin (float): Net profit margin (%)
                - roe (float): Return on equity (%)
                - roa (float): Return on assets (%)
                - roic (float): Return on invested capital (%)

                Liquidity Ratios:
                - current_ratio (float): Current ratio
                - quick_ratio (float): Quick ratio
                - cash_ratio (float): Cash ratio

                Efficiency Ratios:
                - asset_turnover (float): Asset turnover ratio
                - inventory_turnover (float): Inventory turnover ratio
                - receivables_turnover (float): Receivables turnover ratio

                Leverage Ratios:
                - debt_to_equity (float): Debt-to-equity ratio
                - debt_to_assets (float): Debt-to-assets ratio
                - interest_coverage (float): Interest coverage ratio

                Growth Metrics:
                - revenue_growth (float): Revenue growth rate (%)
                - earnings_growth (float): Earnings growth rate (%)
                - book_value_growth (float): Book value growth rate (%)

                Market Ratios:
                - pe_ratio (float): Price-to-earnings ratio
                - pb_ratio (float): Price-to-book ratio
                - ps_ratio (float): Price-to-sales ratio
                - ev_ebitda (float): EV/EBITDA ratio

                Additional fields with metadata:
                - report_date (datetime): Latest report date
                - calculation_method (str): Methodology used
                - data_quality (str): Quality indicator

        Raises:
            QDBError: If financial indicators cannot be retrieved.

        Examples:
            Analyze profitability:
            >>> client = LightweightQDBClient()
            >>> indicators = client.get_financial_indicators("000001")
            >>> print(f"ROE: {indicators['roe']:.2f}%")
            >>> print(f"ROA: {indicators['roa']:.2f}%")
            >>> print(f"ROIC: {indicators['roic']:.2f}%")

            Check financial health:
            >>> indicators = client.get_financial_indicators("600000")
            >>> print(f"Current Ratio: {indicators['current_ratio']:.2f}")
            >>> print(f"Debt/Equity: {indicators['debt_to_equity']:.2f}")
            >>> print(f"Interest Coverage: {indicators['interest_coverage']:.2f}")

            Evaluate growth:
            >>> indicators = client.get_financial_indicators("300001")
            >>> print(f"Revenue Growth: {indicators['revenue_growth']:.2f}%")
            >>> print(f"Earnings Growth: {indicators['earnings_growth']:.2f}%")

        Note:
            - Indicators are calculated from latest quarterly reports
            - Growth rates typically compare year-over-year
            - Some ratios may be None if data is unavailable
            - Data is cached for 24 hours
            - Calculation methods may vary by indicator type
        """
        try:
            financial_service = self._get_service_manager().get_financial_data_service()
            return financial_service.get_financial_indicators(symbol)
        except Exception as e:
            raise QDBError(f"Failed to get financial indicators: {str(e)}")

    def cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics.

        Retrieves detailed statistics about cache usage, hit rates, and
        performance metrics to help monitor and optimize data access patterns.

        Returns:
            Dict[str, Any]: Cache statistics containing:
                - total_requests (int): Total number of data requests
                - cache_hits (int): Number of requests served from cache
                - cache_misses (int): Number of requests requiring fresh data
                - hit_rate (float): Cache hit rate as percentage (0-100)
                - cache_size_mb (float): Current cache size in megabytes
                - cache_entries (int): Number of cached entries
                - oldest_entry (datetime): Timestamp of oldest cached entry
                - newest_entry (datetime): Timestamp of newest cached entry
                - avg_response_time_ms (float): Average response time in milliseconds
                - cache_response_time_ms (float): Average cache response time
                - fresh_data_response_time_ms (float): Average fresh data response time
                - memory_usage_mb (float): Memory usage by cache
                - disk_usage_mb (float): Disk usage by cache files
                - cleanup_count (int): Number of cache cleanup operations
                - last_cleanup (datetime): Last cache cleanup timestamp

        Raises:
            QDBError: If cache statistics cannot be retrieved.

        Examples:
            Monitor cache performance:
            >>> client = LightweightQDBClient()
            >>> stats = client.cache_stats()
            >>> print(f"Cache hit rate: {stats['hit_rate']:.1f}%")
            >>> print(f"Cache size: {stats['cache_size_mb']:.1f} MB")
            >>> print(f"Total entries: {stats['cache_entries']}")

            Check response times:
            >>> stats = client.cache_stats()
            >>> print(f"Avg response: {stats['avg_response_time_ms']:.1f}ms")
            >>> print(f"Cache response: {stats['cache_response_time_ms']:.1f}ms")
            >>> print(f"Fresh data: {stats['fresh_data_response_time_ms']:.1f}ms")

            Monitor resource usage:
            >>> stats = client.cache_stats()
            >>> print(f"Memory: {stats['memory_usage_mb']:.1f} MB")
            >>> print(f"Disk: {stats['disk_usage_mb']:.1f} MB")

        Note:
            - Statistics are updated in real-time
            - Hit rate >90% indicates good cache performance
            - Large cache sizes may indicate need for cleanup
            - Response times help identify performance bottlenecks
        """
        try:
            return self._get_service_manager().get_cache_stats()
        except Exception as e:
            raise QDBError(f"Failed to get cache stats: {str(e)}")

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cached data with optional symbol-specific targeting.

        Removes cached data to force fresh data retrieval on next request.
        Can clear all cache or target specific symbols for selective cleanup.

        Args:
            symbol (str, optional): Specific symbol to clear from cache.
                If None, clears all cached data. Example: "000001"

        Raises:
            QDBError: If cache clearing operation fails.

        Examples:
            Clear all cached data:
            >>> client = LightweightQDBClient()
            >>> client.clear_cache()
            >>> print("All cache cleared")

            Clear specific symbol:
            >>> client.clear_cache("000001")
            >>> print("Cache cleared for 000001")

            Clear cache before important analysis:
            >>> # Ensure fresh data for critical analysis
            >>> symbols = ["000001", "600000", "300001"]
            >>> for symbol in symbols:
            ...     client.clear_cache(symbol)
            >>> # Now get fresh data
            >>> data = client.get_multiple_stocks(symbols, days=30)

        Note:
            - Clearing cache will slow down next data requests
            - Use selectively to balance freshness and performance
            - Cache will rebuild automatically on next requests
            - Consider using force_refresh parameters instead for one-time fresh data
        """
        try:
            self._get_service_manager().clear_cache(symbol)
        except Exception as e:
            raise QDBError(f"Failed to clear cache: {str(e)}")
    
    # AKShare compatibility method
    def stock_zh_a_hist(
        self,
        symbol: str,
        period: str = "daily",
        start_date: str = "19700101",
        end_date: str = "20500101",
        adjust: str = "",
    ):
        """Get historical stock data with AKShare-compatible interface.

        Provides backward compatibility with AKShare's stock_zh_a_hist function
        while leveraging QDB's intelligent caching and performance optimizations.
        This method maintains the same parameter names and behavior as AKShare.

        Args:
            symbol (str): Stock symbol in 6-digit format.
                Same format as AKShare. Example: "000001"
            period (str, optional): Data frequency. Options:
                - "daily": Daily data (default, recommended)
                - "weekly": Weekly data
                - "monthly": Monthly data
                Note: Only "daily" is fully supported currently
            start_date (str, optional): Start date in YYYYMMDD format.
                Default: "19700101" (earliest available)
            end_date (str, optional): End date in YYYYMMDD format.
                Default: "20500101" (far future, gets latest available)
            adjust (str, optional): Price adjustment type.
                Same options as get_stock_data(): "", "qfq", "hfq"

        Returns:
            pd.DataFrame: Historical stock data with AKShare-compatible structure:
                - 日期 (datetime): Trading date
                - 开盘 (float): Opening price
                - 收盘 (float): Closing price
                - 最高 (float): Highest price
                - 最低 (float): Lowest price
                - 成交量 (int): Trading volume
                - 成交额 (float): Trading amount
                - 振幅 (float): Price amplitude (%)
                - 涨跌幅 (float): Price change (%)
                - 涨跌额 (float): Price change amount
                - 换手率 (float): Turnover rate (%)

        Raises:
            QDBError: If data cannot be retrieved using AKShare-compatible interface.

        Examples:
            Basic usage (AKShare style):
            >>> client = LightweightQDBClient()
            >>> df = client.stock_zh_a_hist("000001")
            >>> print(df.head())

            With date range:
            >>> df = client.stock_zh_a_hist(
            ...     "600000",
            ...     start_date="20240101",
            ...     end_date="20240201"
            ... )

            With price adjustment:
            >>> df = client.stock_zh_a_hist("300001", adjust="qfq")

        Note:
            - Maintains AKShare column names in Chinese
            - Benefits from QDB's intelligent caching
            - Recommended to use get_stock_data() for new code
            - This method is for migration compatibility only
            - Performance is significantly better than original AKShare
        """
        try:
            stock_service = self._get_service_manager().get_stock_data_service()
            return stock_service.stock_zh_a_hist(symbol, period, start_date, end_date, adjust)
        except Exception as e:
            raise QDBError(f"Failed to get stock data (AKShare compatible): {str(e)}")


# Global lightweight client instance
_global_lightweight_client: Optional[LightweightQDBClient] = None


def get_lightweight_client(cache_dir: Optional[str] = None) -> LightweightQDBClient:
    """Get the global lightweight client instance."""
    global _global_lightweight_client
    
    if _global_lightweight_client is None:
        _global_lightweight_client = LightweightQDBClient(cache_dir)
    
    return _global_lightweight_client


def reset_lightweight_client():
    """Reset the global lightweight client (mainly for testing)."""
    global _global_lightweight_client
    _global_lightweight_client = None

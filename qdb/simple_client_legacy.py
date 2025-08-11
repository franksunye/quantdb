"""
QDB Simplified Client - Standalone Version

Does not depend on core modules, directly uses AKShare and SQLite
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
import pandas as pd
from datetime import datetime, timedelta

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("⚠️ AKShare not installed, some features unavailable")

from .exceptions import QDBError, CacheError, DataError


class LegacySimpleQDBClient:
    """Simplified QDB client, standalone implementation"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize simplified client

        Args:
            cache_dir: Cache directory path
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.qdb_cache")
        self._ensure_cache_dir()
        self.db_path = os.path.join(self.cache_dir, "qdb_simple.db")
        self._init_database()
        
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create stock data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            ''')
            
            # Create index
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_data(symbol, date)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            raise CacheError(f"Database initialization failed: {str(e)}")
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
        adjust: str = ""
    ) -> pd.DataFrame:
        """
        Get stock historical data

        Args:
            symbol: Stock code (supports both A-shares and HK stocks)
            start_date: Start date, format "20240101"
            end_date: End date, format "20240201"
            days: Get recent N days data
            adjust: Adjustment type

        Returns:
            Stock data DataFrame
        """
        if not AKSHARE_AVAILABLE:
            raise DataError("AKShare not installed, cannot get stock data")

        try:
            # Handle days parameter
            if days is not None:
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")

            # Try to get from cache first
            cached_data = self._get_cached_data(symbol, start_date, end_date)

            # If cache is incomplete, fetch from AKShare
            if cached_data.empty or len(cached_data) < (days or 5):
                print(f"📡 Fetching {symbol} data from AKShare...")

                # Detect market and use appropriate AKShare function
                market = self._classify_market(symbol)

                if market == 'HKEX':
                    # Use HK stock API - don't pass dates for better reliability
                    fresh_data = ak.stock_hk_hist(
                        symbol=symbol,
                        period="daily"
                    )
                    # Filter by date range if we got data
                    if not fresh_data.empty and start_date and end_date:
                        try:
                            fresh_data['日期'] = pd.to_datetime(fresh_data['日期'])
                            start_dt = pd.to_datetime(start_date)
                            end_dt = pd.to_datetime(end_date)
                            fresh_data = fresh_data[
                                (fresh_data['日期'] >= start_dt) &
                                (fresh_data['日期'] <= end_dt)
                            ]
                        except Exception as e:
                            print(f"⚠️ Date filtering failed: {e}, using all data")
                else:
                    # Use A-share API
                    fresh_data = ak.stock_zh_a_hist(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        adjust=adjust
                    )

                if not fresh_data.empty:
                    # Standardize column names
                    fresh_data = self._standardize_columns(fresh_data)
                    # Save to cache
                    self._save_to_cache(symbol, fresh_data)
                    print(f"✅ Retrieved {len(fresh_data)} records")
                    return fresh_data
                else:
                    print("⚠️ AKShare returned empty data")
                    return cached_data
            else:
                print(f"🚀 Loading {symbol} data from cache ({len(cached_data)} records)")
                return cached_data

        except Exception as e:
            raise DataError(f"Failed to get stock data for {symbol}: {str(e)}")

    def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and data format"""
        try:
            # AKShare column name mapping
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }

            # Rename columns
            data_copy = data.copy()
            for chinese_name, english_name in column_mapping.items():
                if chinese_name in data_copy.columns:
                    data_copy.rename(columns={chinese_name: english_name}, inplace=True)

            # Set date index
            if 'date' in data_copy.columns:
                data_copy['date'] = pd.to_datetime(data_copy['date'])
                data_copy.set_index('date', inplace=True)

            return data_copy

        except Exception as e:
            print(f"⚠️ Data standardization failed: {e}")
            return data
    
    def _get_cached_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get data from cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT date, open, high, low, close, volume
                FROM stock_data 
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date
            '''
            
            df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
            return df
            
        except Exception as e:
            print(f"⚠️ Cache read failed: {e}")
            return pd.DataFrame()

    def _save_to_cache(self, symbol: str, data: pd.DataFrame):
        """Save data to cache"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Prepare data
            data_to_save = data.copy()
            data_to_save['symbol'] = symbol

            # Handle date index
            if hasattr(data_to_save.index, 'strftime'):
                data_to_save['date'] = data_to_save.index.strftime('%Y%m%d')
            else:
                # If no date index, generate dates using row numbers
                from datetime import datetime, timedelta
                base_date = datetime.now()
                data_to_save['date'] = [
                    (base_date - timedelta(days=len(data_to_save)-i-1)).strftime('%Y%m%d')
                    for i in range(len(data_to_save))
                ]

            # Select required columns
            columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
            available_columns = [col for col in columns if col in data_to_save.columns]

            if available_columns:
                data_to_save[available_columns].to_sql(
                    'stock_data',
                    conn,
                    if_exists='append',
                    index=False
                )

            conn.close()
            print(f"💾 Cached {len(data_to_save)} records")

        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")
    
    def get_multiple_stocks(
        self,
        symbols: List[str],
        days: int = 30,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """Get multiple stocks data in batch"""
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.get_stock_data(symbol, days=days, **kwargs)
            except Exception as e:
                print(f"⚠️ Failed to get data for {symbol}: {e}")
                result[symbol] = pd.DataFrame()
        return result

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """Get basic asset information"""
        return {
            "symbol": symbol,
            "name": f"Stock {symbol}",
            "market": "A-Share" if symbol.startswith(('0', '3', '6')) else "Unknown",
            "status": "Active"
        }
    
    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Calculate cache size
            cache_size = 0
            if Path(self.cache_dir).exists():
                cache_size = sum(
                    f.stat().st_size for f in Path(self.cache_dir).rglob('*') if f.is_file()
                ) / (1024 * 1024)

            # Get database statistics
            record_count = 0
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM stock_data')
                record_count = cursor.fetchone()[0]
                conn.close()

            return {
                "cache_dir": self.cache_dir,
                "cache_size_mb": round(cache_size, 2),
                "total_records": record_count,
                "akshare_available": AKSHARE_AVAILABLE,
                "status": "Running"
            }

        except Exception as e:
            raise CacheError(f"Failed to get cache statistics: {str(e)}")
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache"""
        try:
            if symbol:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM stock_data WHERE symbol = ?', (symbol,))
                conn.commit()
                conn.close()
                print(f"✅ Cleared cache for {symbol}")
            else:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    self._init_database()
                    print("✅ Cache cleared")

        except Exception as e:
            raise CacheError(f"Failed to clear cache: {str(e)}")

    def get_realtime_data(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get realtime stock data (simplified implementation)

        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with realtime stock data
        """
        try:
            if not AKSHARE_AVAILABLE:
                return {
                    'symbol': symbol,
                    'error': 'AKShare not available',
                    'cache_hit': False,
                    'timestamp': datetime.now().isoformat()
                }

            # For simplified client, we'll use stock_zh_a_spot directly
            import akshare as ak

            # Get all realtime data
            try:
                df = ak.stock_zh_a_spot()
            except Exception as e:
                # If AKShare fails, return mock data for demonstration
                print(f"⚠️ AKShare realtime data unavailable, using mock data: {e}")
                return self._get_mock_realtime_data(symbol)

            # Clean symbol
            clean_symbol = symbol
            if "." in clean_symbol:
                clean_symbol = clean_symbol.split(".")[0]
            if clean_symbol.lower().startswith("sh") or clean_symbol.lower().startswith("sz"):
                clean_symbol = clean_symbol[2:]

            # Filter for our symbol
            symbol_data = df[df['代码'] == clean_symbol]

            if symbol_data.empty:
                return {
                    'symbol': symbol,
                    'error': 'Symbol not found',
                    'cache_hit': False,
                    'timestamp': datetime.now().isoformat()
                }

            # Convert to our format
            row = symbol_data.iloc[0]
            return {
                'symbol': symbol,
                'name': row.get('名称', f'Stock {symbol}'),
                'price': float(row.get('最新价', 0)),
                'open': float(row.get('今开', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'prev_close': float(row.get('昨收', 0)),
                'change': float(row.get('涨跌额', 0)),
                'pct_change': float(row.get('涨跌幅', 0)),
                'volume': float(row.get('成交量', 0)),
                'turnover': float(row.get('成交额', 0)),
                'timestamp': datetime.now().isoformat(),
                'cache_hit': False
            }

        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'cache_hit': False,
                'timestamp': datetime.now().isoformat()
            }

    def get_realtime_data_batch(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get realtime data for multiple stocks (simplified implementation)

        Args:
            symbols: List of stock symbols
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with symbol as key and realtime data as value
        """
        result = {}

        try:
            if not AKSHARE_AVAILABLE:
                for symbol in symbols:
                    result[symbol] = {
                        'symbol': symbol,
                        'error': 'AKShare not available',
                        'cache_hit': False,
                        'timestamp': datetime.now().isoformat()
                    }
                return result

            # Get all realtime data once
            import akshare as ak
            try:
                df = ak.stock_zh_a_spot()
            except Exception as e:
                # If AKShare fails, return mock data for demonstration
                print(f"⚠️ AKShare realtime data unavailable, using mock data: {e}")
                for symbol in symbols:
                    result[symbol] = self._get_mock_realtime_data(symbol)
                return result

            for symbol in symbols:
                try:
                    # Clean symbol
                    clean_symbol = symbol
                    if "." in clean_symbol:
                        clean_symbol = clean_symbol.split(".")[0]
                    if clean_symbol.lower().startswith("sh") or clean_symbol.lower().startswith("sz"):
                        clean_symbol = clean_symbol[2:]

                    # Filter for this symbol
                    symbol_data = df[df['代码'] == clean_symbol]

                    if not symbol_data.empty:
                        row = symbol_data.iloc[0]
                        result[symbol] = {
                            'symbol': symbol,
                            'name': row.get('名称', f'Stock {symbol}'),
                            'price': float(row.get('最新价', 0)),
                            'open': float(row.get('今开', 0)),
                            'high': float(row.get('最高', 0)),
                            'low': float(row.get('最低', 0)),
                            'prev_close': float(row.get('昨收', 0)),
                            'change': float(row.get('涨跌额', 0)),
                            'pct_change': float(row.get('涨跌幅', 0)),
                            'volume': float(row.get('成交量', 0)),
                            'turnover': float(row.get('成交额', 0)),
                            'timestamp': datetime.now().isoformat(),
                            'cache_hit': False
                        }
                    else:
                        result[symbol] = {
                            'symbol': symbol,
                            'error': 'Symbol not found',
                            'cache_hit': False,
                            'timestamp': datetime.now().isoformat()
                        }

                except Exception as e:
                    result[symbol] = {
                        'symbol': symbol,
                        'error': str(e),
                        'cache_hit': False,
                        'timestamp': datetime.now().isoformat()
                    }

            return result

        except Exception as e:
            # Return error for all symbols
            for symbol in symbols:
                result[symbol] = {
                    'symbol': symbol,
                    'error': str(e),
                    'cache_hit': False,
                    'timestamp': datetime.now().isoformat()
                }
            return result

    def _get_mock_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """
        Generate mock realtime data for demonstration purposes.

        Args:
            symbol: Stock symbol

        Returns:
            Mock realtime data dictionary
        """
        import random

        # Mock data based on symbol
        base_prices = {
            '000001': 10.50,  # 平安银行
            '000002': 25.30,  # 万科A
            '600000': 8.20,   # 浦发银行
            '600036': 35.80,  # 招商银行
        }

        base_price = base_prices.get(symbol, 20.00)
        change_pct = random.uniform(-3.0, 3.0)
        change = base_price * change_pct / 100
        current_price = base_price + change

        return {
            'symbol': symbol,
            'name': f'Mock Stock {symbol}',
            'price': round(current_price, 2),
            'open': round(base_price + random.uniform(-0.5, 0.5), 2),
            'high': round(current_price + random.uniform(0, 1.0), 2),
            'low': round(current_price - random.uniform(0, 1.0), 2),
            'prev_close': base_price,
            'change': round(change, 2),
            'pct_change': round(change_pct, 2),
            'volume': random.randint(100000, 10000000),
            'turnover': random.randint(1000000, 100000000),
            'timestamp': datetime.now().isoformat(),
            'cache_hit': False,
            'is_mock': True
        }

    def get_stock_list(self, market: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get stock list with market filtering and daily caching.

        Args:
            market: Market filter ('SHSE', 'SZSE', 'HKEX', or None for all markets)
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of dictionaries containing stock information
        """
        try:
            if not AKSHARE_AVAILABLE:
                print("⚠️ AKShare not available, returning mock stock list")
                return self._get_mock_stock_list(market)

            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_stock_list(market)
                if cached_data:
                    print(f"✅ Using cached stock list ({len(cached_data)} stocks)")
                    return cached_data

            # Fetch fresh data from AKShare
            print("🔄 Fetching fresh stock list from AKShare...")
            import akshare as ak

            try:
                df = ak.stock_zh_a_spot_em()
            except Exception as e:
                print(f"⚠️ AKShare stock list unavailable, using mock data: {e}")
                return self._get_mock_stock_list(market)

            if df.empty:
                print("⚠️ No stock list data available")
                return []

            # Process and filter data
            stocks = []
            for _, row in df.iterrows():
                try:
                    symbol = str(row.get('代码', '')).strip()
                    if not symbol:
                        continue

                    # Classify market
                    stock_market = self._classify_market(symbol)

                    # Apply market filter
                    if market and market.upper() != stock_market:
                        continue

                    stock_data = {
                        'symbol': symbol,
                        'name': str(row.get('名称', 'Unknown')).strip(),
                        'market': stock_market,
                        'price': float(row.get('最新价', 0)) if row.get('最新价') else None,
                        'pct_change': float(row.get('涨跌幅', 0)) if row.get('涨跌幅') else None,
                        'change': float(row.get('涨跌额', 0)) if row.get('涨跌额') else None,
                        'volume': float(row.get('成交量', 0)) if row.get('成交量') else None,
                        'turnover': float(row.get('成交额', 0)) if row.get('成交额') else None,
                        'cache_date': datetime.now().date().isoformat(),
                        'is_active': True
                    }
                    stocks.append(stock_data)

                except Exception as e:
                    print(f"⚠️ Error processing stock {row.get('代码', 'unknown')}: {e}")
                    continue

            # Save to cache
            self._save_stock_list_to_cache(stocks)

            print(f"✅ Retrieved {len(stocks)} stocks for market: {market or 'all'}")
            return stocks

        except Exception as e:
            print(f"⚠️ Error getting stock list: {e}")
            # Try to return cached data as fallback
            try:
                cached_data = self._get_cached_stock_list(market)
                if cached_data:
                    print(f"✅ Using cached data as fallback ({len(cached_data)} stocks)")
                    return cached_data
            except:
                pass

            # Final fallback to mock data
            return self._get_mock_stock_list(market)

    def _classify_market(self, symbol: str) -> str:
        """
        Classify stock market based on symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Market code ('SHSE', 'SZSE', 'HKEX')
        """
        if not symbol:
            return 'UNKNOWN'

        symbol = str(symbol).strip()

        # Hong Kong Exchange (HKEX) - 5 digit codes (check first)
        if len(symbol) == 5 and symbol.isdigit():
            return 'HKEX'

        # Shanghai Stock Exchange (SHSE)
        elif (symbol.startswith('60') or
              symbol.startswith('68') or
              symbol.startswith('90')):
            return 'SHSE'

        # Shenzhen Stock Exchange (SZSE)
        elif (symbol.startswith('00') or
              symbol.startswith('30') or
              symbol.startswith('20')):
            return 'SZSE'

        # Default to SZSE for other patterns
        else:
            return 'SZSE'

    def _get_cached_stock_list(self, market: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get stock list from cache if fresh (today's data).

        Args:
            market: Market filter

        Returns:
            Cached stock list or None if not fresh
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if stock_list table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='stock_list'
            """)

            if not cursor.fetchone():
                conn.close()
                return None

            # Check for today's data
            today = datetime.now().date().isoformat()

            query = """
                SELECT symbol, name, market, price, pct_change, change,
                       volume, turnover, cache_date, is_active
                FROM stock_list
                WHERE cache_date = ? AND is_active = 1
            """
            params = [today]

            # Apply market filter
            if market:
                query += " AND market = ?"
                params.append(market.upper())

            query += " ORDER BY symbol"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return None

            # Convert to list of dictionaries
            stocks = []
            for row in rows:
                stocks.append({
                    'symbol': row[0],
                    'name': row[1],
                    'market': row[2],
                    'price': row[3],
                    'pct_change': row[4],
                    'change': row[5],
                    'volume': row[6],
                    'turnover': row[7],
                    'cache_date': row[8],
                    'is_active': bool(row[9])
                })

            return stocks

        except Exception as e:
            print(f"⚠️ Error reading stock list cache: {e}")
            return None

    def _save_stock_list_to_cache(self, stocks: List[Dict[str, Any]]):
        """
        Save stock list to cache.

        Args:
            stocks: List of stock dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create stock_list table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    price REAL,
                    pct_change REAL,
                    change REAL,
                    volume REAL,
                    turnover REAL,
                    cache_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, cache_date)
                )
            ''')

            # Clear today's data first
            today = datetime.now().date().isoformat()
            cursor.execute("DELETE FROM stock_list WHERE cache_date = ?", (today,))

            # Insert new data
            for stock in stocks:
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_list
                    (symbol, name, market, price, pct_change, change,
                     volume, turnover, cache_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock['symbol'],
                    stock['name'],
                    stock['market'],
                    stock.get('price'),
                    stock.get('pct_change'),
                    stock.get('change'),
                    stock.get('volume'),
                    stock.get('turnover'),
                    stock['cache_date'],
                    1 if stock.get('is_active', True) else 0
                ))

            conn.commit()
            conn.close()
            print(f"✅ Saved {len(stocks)} stocks to cache")

        except Exception as e:
            print(f"⚠️ Error saving stock list to cache: {e}")

    def _get_mock_stock_list(self, market: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate mock stock list for demonstration.

        Args:
            market: Market filter

        Returns:
            Mock stock list
        """
        mock_stocks = [
            {'symbol': '000001', 'name': 'Ping An Bank', 'market': 'SZSE'},
            {'symbol': '000002', 'name': 'China Vanke', 'market': 'SZSE'},
            {'symbol': '600000', 'name': 'Shanghai Pudong Development Bank', 'market': 'SHSE'},
            {'symbol': '600036', 'name': 'China Merchants Bank', 'market': 'SHSE'},
            {'symbol': '600519', 'name': 'Kweichow Moutai', 'market': 'SHSE'},
            {'symbol': '000858', 'name': 'Wuliangye Yibin', 'market': 'SZSE'},
            {'symbol': '300015', 'name': 'Aier Eye Hospital', 'market': 'SZSE'},
            {'symbol': '00700', 'name': 'Tencent Holdings', 'market': 'HKEX'},
            {'symbol': '09988', 'name': 'Alibaba Group-SW', 'market': 'HKEX'},
        ]

        # Apply market filter
        if market:
            market_upper = market.upper()
            mock_stocks = [s for s in mock_stocks if s['market'] == market_upper]

        # Add mock data
        import random
        for stock in mock_stocks:
            stock.update({
                'price': round(random.uniform(10, 200), 2),
                'pct_change': round(random.uniform(-5, 5), 2),
                'change': round(random.uniform(-10, 10), 2),
                'volume': random.randint(100000, 10000000),
                'turnover': random.randint(1000000, 100000000),
                'cache_date': datetime.now().date().isoformat(),
                'is_active': True,
                'is_mock': True
            })

        return mock_stocks

    def get_financial_summary(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get financial summary data (simplified implementation)

        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary containing financial summary data
        """
        try:
            if not AKSHARE_AVAILABLE:
                return {
                    'symbol': symbol,
                    'error': 'AKShare not available',
                    'timestamp': datetime.now().isoformat()
                }

            print(f"📊 Getting financial summary for {symbol}...")

            # Use AKShare to get financial summary
            df = ak.stock_financial_abstract(symbol=symbol)

            if df.empty:
                print(f"⚠️ No financial summary data available for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'No financial summary data available',
                    'timestamp': datetime.now().isoformat()
                }

            # Process the data into a simplified format
            quarters = []
            date_columns = [col for col in df.columns if col not in ['选项', '指标']]

            # Get latest 4 quarters
            for date_col in date_columns[:4]:
                quarter_data = {'period': date_col}

                for _, row in df.iterrows():
                    indicator = row['指标']
                    value = row.get(date_col)

                    if value is not None and not pd.isna(value):
                        # Map key indicators
                        if indicator == '归母净利润':
                            quarter_data['net_profit'] = float(value)
                        elif indicator == '营业总收入':
                            quarter_data['total_revenue'] = float(value)
                        elif indicator == '营业成本':
                            quarter_data['operating_cost'] = float(value)
                        elif indicator == '净资产收益率':
                            quarter_data['roe'] = float(value)
                        elif indicator == '总资产收益率':
                            quarter_data['roa'] = float(value)

                quarters.append(quarter_data)

            result = {
                'symbol': symbol,
                'data_type': 'financial_summary',
                'quarters': quarters,
                'count': len(quarters),
                'timestamp': datetime.now().isoformat()
            }

            print(f"✅ Retrieved financial summary for {symbol} ({len(quarters)} quarters)")
            return result

        except Exception as e:
            print(f"⚠️ Error getting financial summary for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_financial_indicators(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get financial indicators data (simplified implementation)

        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary containing financial indicators data
        """
        try:
            if not AKSHARE_AVAILABLE:
                return {
                    'symbol': symbol,
                    'error': 'AKShare not available',
                    'timestamp': datetime.now().isoformat()
                }

            print(f"📈 Getting financial indicators for {symbol}...")

            # Use AKShare to get financial indicators
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if df.empty:
                print(f"⚠️ No financial indicators data available for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'No financial indicators data available',
                    'timestamp': datetime.now().isoformat()
                }

            # Process the indicators data
            result = {
                'symbol': symbol,
                'data_type': 'financial_indicators',
                'data_shape': f"{df.shape[0]}x{df.shape[1]}",
                'columns': list(df.columns)[:10],  # First 10 columns as sample
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
                'timestamp': datetime.now().isoformat()
            }

            print(f"✅ Retrieved financial indicators for {symbol} (shape: {df.shape})")
            return result

        except Exception as e:
            print(f"⚠️ Error getting financial indicators for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_index_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Get historical index data

        Args:
            symbol: Index symbol (e.g., '000001', '399001')
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            period: Data frequency ('daily', 'weekly', 'monthly')
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            DataFrame with historical index data
        """
        try:
            if not AKSHARE_AVAILABLE:
                print("⚠️ AKShare not available, returning mock index data")
                return self._get_mock_index_data(symbol, start_date, end_date)

            # For simplified client, we'll use index_zh_a_hist directly
            import akshare as ak

            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            # Clean symbol
            clean_symbol = symbol
            if "." in clean_symbol:
                clean_symbol = clean_symbol.split(".")[0]
            if clean_symbol.lower().startswith("sh") or clean_symbol.lower().startswith("sz"):
                clean_symbol = clean_symbol[2:]

            try:
                df = ak.index_zh_a_hist(
                    symbol=clean_symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                print(f"⚠️ AKShare index data unavailable, using mock data: {e}")
                return self._get_mock_index_data(symbol, start_date, end_date)

            if df.empty:
                print("⚠️ No index data available")
                return self._get_mock_index_data(symbol, start_date, end_date)

            # Standardize column names
            df = self._standardize_index_columns(df)
            print(f"✅ Retrieved {len(df)} rows of index data for {symbol}")
            return df

        except Exception as e:
            raise DataError(f"Failed to get index data for {symbol}: {str(e)}")

    def get_index_realtime(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get realtime index data

        Args:
            symbol: Index symbol
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with realtime index data
        """
        try:
            if not AKSHARE_AVAILABLE:
                return {
                    'symbol': symbol,
                    'error': 'AKShare not available',
                    'cache_hit': False,
                    'timestamp': datetime.now().isoformat()
                }

            # For simplified client, we'll use stock_zh_index_spot_em directly
            import akshare as ak

            try:
                df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
            except Exception as e:
                print(f"⚠️ AKShare realtime index data unavailable, using mock data: {e}")
                return self._get_mock_index_realtime_data(symbol)

            # Clean symbol
            clean_symbol = symbol
            if "." in clean_symbol:
                clean_symbol = clean_symbol.split(".")[0]
            if clean_symbol.lower().startswith("sh") or clean_symbol.lower().startswith("sz"):
                clean_symbol = clean_symbol[2:]

            # Filter for the specific symbol
            symbol_df = df[df['代码'] == clean_symbol] if '代码' in df.columns else pd.DataFrame()

            if symbol_df.empty:
                print(f"⚠️ Index {clean_symbol} not found in realtime data, using mock data")
                return self._get_mock_index_realtime_data(symbol)

            # Convert to dictionary
            data = symbol_df.iloc[0].to_dict()

            # Standardize field names
            standardized_data = {
                'symbol': data.get('代码', symbol),
                'name': data.get('名称', f'Index {symbol}'),
                'price': data.get('最新价', 0.0),
                'change': data.get('涨跌额', 0.0),
                'pct_change': data.get('涨跌幅', 0.0),
                'volume': data.get('成交量', 0.0),
                'turnover': data.get('成交额', 0.0),
                'high': data.get('最高', 0.0),
                'low': data.get('最低', 0.0),
                'open': data.get('今开', 0.0),
                'prev_close': data.get('昨收', 0.0),
                'amplitude': data.get('振幅', 0.0),
                'cache_hit': False,
                'timestamp': datetime.now().isoformat(),
                'is_trading_hours': self._is_trading_hours()
            }

            print(f"✅ Retrieved realtime index data for {symbol}")
            return standardized_data

        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'cache_hit': False,
                'timestamp': datetime.now().isoformat()
            }

    def get_index_list(self, category: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get index list with category filtering and daily caching

        Args:
            category: Index category filter
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of dictionaries containing index information
        """
        try:
            if not AKSHARE_AVAILABLE:
                print("⚠️ AKShare not available, returning mock index list")
                return self._get_mock_index_list(category)

            # For simplified client, we'll use stock_zh_index_spot_em directly
            import akshare as ak

            categories = ["沪深重要指数", "上证系列指数", "深证系列指数", "中证系列指数"]
            if category:
                categories = [category]

            all_indexes = []

            for cat in categories:
                try:
                    df = ak.stock_zh_index_spot_em(symbol=cat)
                    if df is not None and not df.empty:
                        # Add category information
                        df = df.copy()
                        df['category'] = cat
                        all_indexes.append(df)
                except Exception as e:
                    print(f"⚠️ Failed to get indexes for category {cat}: {e}")
                    continue

            if not all_indexes:
                print("⚠️ No index list data available, using mock data")
                return self._get_mock_index_list(category)

            # Combine all categories
            df = pd.concat(all_indexes, ignore_index=True)

            # Convert to list of dictionaries
            index_list = []
            for _, row in df.iterrows():
                index_data = {
                    'symbol': row.get('代码', ''),
                    'name': row.get('名称', ''),
                    'category': row.get('category', 'Unknown'),
                    'price': row.get('最新价'),
                    'pct_change': row.get('涨跌幅'),
                    'change': row.get('涨跌额'),
                    'volume': row.get('成交量'),
                    'turnover': row.get('成交额'),
                    'cache_date': datetime.now().date().isoformat(),
                    'is_active': True
                }
                index_list.append(index_data)

            print(f"✅ Retrieved {len(index_list)} indexes")
            return index_list

        except Exception as e:
            # Final fallback to mock data
            return self._get_mock_index_list(category)


    def _standardize_index_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize index data column names.

        Args:
            df: DataFrame with Chinese column names

        Returns:
            DataFrame with standardized English column names
        """
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'turnover',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover_rate'
        }

        # Rename columns that exist
        for chinese_name, english_name in column_mapping.items():
            if chinese_name in df.columns:
                df = df.rename(columns={chinese_name: english_name})

        return df

    def _get_mock_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate mock index data for testing."""
        import random
        import numpy as np

        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y%m%d')
        end_dt = datetime.strptime(end_date, '%Y%m%d')

        # Generate date range (business days only)
        dates = pd.bdate_range(start=start_dt, end=end_dt)

        data = []
        base_price = 3000.0  # Base index value

        for i, date in enumerate(dates):
            # Simulate price movement
            if i == 0:
                open_price = base_price
            else:
                open_price = data[i-1]['close']

            # Random daily movement
            change_pct = np.random.normal(0, 0.02)  # 2% daily volatility
            close_price = open_price * (1 + change_pct)

            high = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))

            volume = random.randint(100000000, 500000000)  # Index volume

            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'turnover': round(close_price * volume / 1000000, 2),  # In millions
                'amplitude': round((high - low) / close_price * 100, 2),
                'pct_change': round(change_pct * 100, 2),
                'change': round(close_price - open_price, 2)
            })

        df = pd.DataFrame(data)
        print(f"Generated {len(df)} rows of mock index data for {symbol}")
        return df

    def _get_mock_index_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock realtime index data."""
        import random

        base_price = 3000.0
        change_pct = random.uniform(-3, 3)
        price = base_price * (1 + change_pct / 100)

        return {
            'symbol': symbol,
            'name': f'Mock Index {symbol}',
            'price': round(price, 2),
            'open': round(price * 0.995, 2),
            'high': round(price * 1.01, 2),
            'low': round(price * 0.99, 2),
            'prev_close': round(base_price, 2),
            'change': round(price - base_price, 2),
            'pct_change': round(change_pct, 2),
            'amplitude': round(random.uniform(0.5, 3.0), 2),
            'volume': random.randint(100000000, 500000000),
            'turnover': random.randint(10000000000, 50000000000),
            'cache_hit': False,
            'timestamp': datetime.now().isoformat(),
            'is_trading_hours': self._is_trading_hours(),
            'is_mock': True
        }

    def _get_mock_index_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate mock index list."""
        import random

        mock_indexes = [
            {'symbol': '000001', 'name': 'Shanghai Composite Index', 'category': 'Major Indices'},
            {'symbol': '399001', 'name': 'Shenzhen Component Index', 'category': 'Major Indices'},
            {'symbol': '399006', 'name': 'ChiNext Index', 'category': 'Major Indices'},
            {'symbol': '000300', 'name': 'CSI 300 Index', 'category': 'Major Indices'},
            {'symbol': '000016', 'name': 'SSE 50 Index', 'category': 'SSE Indices'},
            {'symbol': '000905', 'name': 'CSI 500 Index', 'category': 'CSI Indices'},
            {'symbol': '399005', 'name': 'SZSE SME 100 Index', 'category': 'SZSE Indices'},
        ]

        # Apply category filter
        if category:
            mock_indexes = [idx for idx in mock_indexes if idx['category'] == category]

        # Add mock market data
        for index in mock_indexes:
            base_price = random.uniform(2000, 4000)
            change_pct = random.uniform(-3, 3)

            index.update({
                'price': round(base_price, 2),
                'pct_change': round(change_pct, 2),
                'change': round(base_price * change_pct / 100, 2),
                'volume': random.randint(100000000, 500000000),
                'turnover': random.randint(10000000000, 50000000000),
                'cache_date': datetime.now().date().isoformat(),
                'is_active': True,
                'is_mock': True
            })

        return mock_indexes

    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours."""
        try:
            now = datetime.now()
            current_time = now.time()

            # A-share trading hours: 9:30-11:30, 13:00-15:00 (Monday-Friday)
            if now.weekday() >= 5:  # Weekend
                return False

            morning_start = datetime.strptime("09:30", "%H:%M").time()
            morning_end = datetime.strptime("11:30", "%H:%M").time()
            afternoon_start = datetime.strptime("13:00", "%H:%M").time()
            afternoon_end = datetime.strptime("15:00", "%H:%M").time()

            return (morning_start <= current_time <= morning_end) or \
                   (afternoon_start <= current_time <= afternoon_end)

        except Exception:
            return True  # Default to trading hours for safety


# Global simplified client instance
_simple_client: Optional[SimpleQDBClient] = None

def get_simple_client() -> SimpleQDBClient:
    """Get global simplified client instance"""
    global _simple_client
    if _simple_client is None:
        _simple_client = SimpleQDBClient()
    return _simple_client

# Simplified public API
def simple_get_stock_data(symbol: str, **kwargs) -> pd.DataFrame:
    """Simplified version to get stock data"""
    return get_simple_client().get_stock_data(symbol, **kwargs)

def simple_cache_stats() -> Dict[str, Any]:
    """Simplified version to get cache statistics"""
    return get_simple_client().cache_stats()

def simple_get_asset_info(symbol: str) -> Dict[str, Any]:
    """Simplified version to get asset information"""
    return get_simple_client().get_asset_info(symbol)

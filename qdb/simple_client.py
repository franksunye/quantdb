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


class SimpleQDBClient:
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
            symbol: Stock code
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
            # 处理days参数
            if days is not None:
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")
            
            # 首先尝试从缓存获取
            cached_data = self._get_cached_data(symbol, start_date, end_date)
            
            # 如果缓存不完整，从AKShare获取
            if cached_data.empty or len(cached_data) < (days or 5):
                print(f"📡 从AKShare获取 {symbol} 数据...")
                fresh_data = ak.stock_zh_a_hist(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )

                if not fresh_data.empty:
                    # 标准化列名
                    fresh_data = self._standardize_columns(fresh_data)
                    # 保存到缓存
                    self._save_to_cache(symbol, fresh_data)
                    print(f"✅ 获取到 {len(fresh_data)} 条数据")
                    return fresh_data
                else:
                    print("⚠️ AKShare返回空数据")
                    return cached_data
            else:
                print(f"🚀 从缓存获取 {symbol} 数据 ({len(cached_data)} 条)")
                return cached_data
                
        except Exception as e:
            raise DataError(f"获取股票数据失败 {symbol}: {str(e)}")

    def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化列名和数据格式"""
        try:
            # AKShare返回的列名映射
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }

            # 重命名列
            data_copy = data.copy()
            for chinese_name, english_name in column_mapping.items():
                if chinese_name in data_copy.columns:
                    data_copy.rename(columns={chinese_name: english_name}, inplace=True)

            # 设置日期索引
            if 'date' in data_copy.columns:
                data_copy['date'] = pd.to_datetime(data_copy['date'])
                data_copy.set_index('date', inplace=True)

            return data_copy

        except Exception as e:
            print(f"⚠️ 数据标准化失败: {e}")
            return data
    
    def _get_cached_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从缓存获取数据"""
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
            print(f"⚠️ 缓存读取失败: {e}")
            return pd.DataFrame()
    
    def _save_to_cache(self, symbol: str, data: pd.DataFrame):
        """保存数据到缓存"""
        try:
            conn = sqlite3.connect(self.db_path)

            # 准备数据
            data_to_save = data.copy()
            data_to_save['symbol'] = symbol

            # 处理日期索引
            if hasattr(data_to_save.index, 'strftime'):
                data_to_save['date'] = data_to_save.index.strftime('%Y%m%d')
            else:
                # 如果没有日期索引，使用行号生成日期
                from datetime import datetime, timedelta
                base_date = datetime.now()
                data_to_save['date'] = [
                    (base_date - timedelta(days=len(data_to_save)-i-1)).strftime('%Y%m%d')
                    for i in range(len(data_to_save))
                ]

            # 选择需要的列
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
            print(f"💾 已缓存 {len(data_to_save)} 条数据")

        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")
    
    def get_multiple_stocks(
        self, 
        symbols: List[str], 
        days: int = 30,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """批量获取多只股票数据"""
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.get_stock_data(symbol, days=days, **kwargs)
            except Exception as e:
                print(f"⚠️ 获取 {symbol} 数据失败: {e}")
                result[symbol] = pd.DataFrame()
        return result
    
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """获取资产基本信息"""
        return {
            "symbol": symbol,
            "name": f"股票{symbol}",
            "market": "A股" if symbol.startswith(('0', '3', '6')) else "未知",
            "status": "正常"
        }
    
    def cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            # 计算缓存大小
            cache_size = 0
            if Path(self.cache_dir).exists():
                cache_size = sum(
                    f.stat().st_size for f in Path(self.cache_dir).rglob('*') if f.is_file()
                ) / (1024 * 1024)
            
            # 获取数据库统计
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
            raise CacheError(f"获取缓存统计失败: {str(e)}")
    
    def clear_cache(self, symbol: Optional[str] = None):
        """清除缓存"""
        try:
            if symbol:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM stock_data WHERE symbol = ?', (symbol,))
                conn.commit()
                conn.close()
                print(f"✅ 已清除 {symbol} 的缓存")
            else:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    self._init_database()
                    print("✅ Cache cleared")
                
        except Exception as e:
            raise CacheError(f"清除缓存失败: {str(e)}")

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
            {'symbol': '000001', 'name': '平安银行', 'market': 'SZSE'},
            {'symbol': '000002', 'name': '万科A', 'market': 'SZSE'},
            {'symbol': '600000', 'name': '浦发银行', 'market': 'SHSE'},
            {'symbol': '600036', 'name': '招商银行', 'market': 'SHSE'},
            {'symbol': '600519', 'name': '贵州茅台', 'market': 'SHSE'},
            {'symbol': '000858', 'name': '五粮液', 'market': 'SZSE'},
            {'symbol': '300015', 'name': '爱尔眼科', 'market': 'SZSE'},
            {'symbol': '00700', 'name': '腾讯控股', 'market': 'HKEX'},
            {'symbol': '09988', 'name': '阿里巴巴-SW', 'market': 'HKEX'},
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


# 全局简化客户端实例
_simple_client: Optional[SimpleQDBClient] = None

def get_simple_client() -> SimpleQDBClient:
    """获取全局简化客户端实例"""
    global _simple_client
    if _simple_client is None:
        _simple_client = SimpleQDBClient()
    return _simple_client

# 简化的公开API
def simple_get_stock_data(symbol: str, **kwargs) -> pd.DataFrame:
    """简化版获取股票数据"""
    return get_simple_client().get_stock_data(symbol, **kwargs)

def simple_cache_stats() -> Dict[str, Any]:
    """简化版缓存统计"""
    return get_simple_client().cache_stats()

def simple_get_asset_info(symbol: str) -> Dict[str, Any]:
    """简化版获取资产信息"""
    return get_simple_client().get_asset_info(symbol)

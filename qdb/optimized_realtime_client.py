"""
优化的实时数据客户端实现

这个文件展示了如何优化 SimpleQDBClient 中的实时数据获取功能，
解决当前实现中的性能问题。
"""

import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import akshare as ak

    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


class OptimizedRealtimeClient:
    """优化的实时数据客户端"""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.expanduser("~/.qdb_cache")
        self._ensure_cache_dir()
        self.db_path = os.path.join(self.cache_dir, "realtime_cache.db")
        self._init_realtime_cache()

        # 内存缓存配置
        self.memory_cache = {}
        self.cache_ttl = 60  # 1分钟缓存
        self.trading_hours_ttl = 30  # 交易时间内30秒缓存

        # 批量获取优化
        self.batch_cache = {}
        self.batch_cache_time = None
        self.batch_cache_ttl = 300  # 5分钟批量缓存

        # 线程锁
        self._cache_lock = threading.Lock()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    def _init_realtime_cache(self):
        """初始化实时数据缓存表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS realtime_cache (
                    symbol TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    is_trading_hours BOOLEAN DEFAULT 0
                )
            """
            )

            # 创建索引
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON realtime_cache(timestamp)
            """
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️ 初始化实时缓存失败: {e}")

    def _is_trading_hours(self) -> bool:
        """判断是否在交易时间内"""
        now = datetime.now()
        weekday = now.weekday()

        # 周末不交易
        if weekday >= 5:
            return False

        # 简化的交易时间判断 (9:30-11:30, 13:00-15:00)
        current_time = now.time()
        morning_start = datetime.strptime("09:30", "%H:%M").time()
        morning_end = datetime.strptime("11:30", "%H:%M").time()
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()
        afternoon_end = datetime.strptime("15:00", "%H:%M").time()

        return (
            morning_start <= current_time <= morning_end
            or afternoon_start <= current_time <= afternoon_end
        )

    def _get_cache_ttl(self) -> int:
        """根据交易时间获取缓存TTL"""
        return self.trading_hours_ttl if self._is_trading_hours() else self.cache_ttl

    def _get_from_memory_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从内存缓存获取数据"""
        with self._cache_lock:
            if symbol in self.memory_cache:
                cached_time, cached_data = self.memory_cache[symbol]
                ttl = self._get_cache_ttl()

                if time.time() - cached_time < ttl:
                    cached_data = cached_data.copy()
                    cached_data["cache_hit"] = True
                    cached_data["cache_source"] = "memory"
                    return cached_data
                else:
                    # 过期删除
                    del self.memory_cache[symbol]
        return None

    def _save_to_memory_cache(self, symbol: str, data: Dict[str, Any]):
        """保存到内存缓存"""
        with self._cache_lock:
            self.memory_cache[symbol] = (time.time(), data.copy())

    def _get_from_db_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从数据库缓存获取数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT data, timestamp, is_trading_hours 
                FROM realtime_cache 
                WHERE symbol = ?
            """,
                (symbol,),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                data_str, cached_time, was_trading_hours = result
                ttl = self.trading_hours_ttl if was_trading_hours else self.cache_ttl

                if time.time() - cached_time < ttl:
                    import json

                    cached_data = json.loads(data_str)
                    cached_data["cache_hit"] = True
                    cached_data["cache_source"] = "database"
                    return cached_data

        except Exception as e:
            print(f"⚠️ 数据库缓存读取失败: {e}")

        return None

    def _save_to_db_cache(self, symbol: str, data: Dict[str, Any]):
        """保存到数据库缓存"""
        try:
            import json

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO realtime_cache 
                (symbol, data, timestamp, is_trading_hours)
                VALUES (?, ?, ?, ?)
            """,
                (symbol, json.dumps(data), time.time(), self._is_trading_hours()),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️ 数据库缓存保存失败: {e}")

    def get_realtime_data(
        self, symbol: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        优化的单个股票实时数据获取

        优化点:
        1. 多级缓存 (内存 -> 数据库 -> 网络)
        2. 智能TTL (交易时间内更短的缓存时间)
        3. 更好的错误处理
        """
        if not force_refresh:
            # 尝试内存缓存
            cached_data = self._get_from_memory_cache(symbol)
            if cached_data:
                return cached_data

            # 尝试数据库缓存
            cached_data = self._get_from_db_cache(symbol)
            if cached_data:
                # 同时保存到内存缓存
                self._save_to_memory_cache(symbol, cached_data)
                return cached_data

        # 从网络获取
        try:
            if not AKSHARE_AVAILABLE:
                return self._get_mock_data(symbol)

            # 使用更高效的AKShare接口
            df = ak.stock_zh_a_spot()

            # 清理symbol格式
            clean_symbol = self._clean_symbol(symbol)

            # 查找对应的股票数据
            stock_data = df[df["代码"] == clean_symbol]

            if not stock_data.empty:
                row = stock_data.iloc[0]
                data = self._convert_akshare_data(symbol, row)
                data["cache_hit"] = False
                data["cache_source"] = "network"

                # 保存到缓存
                self._save_to_memory_cache(symbol, data)
                self._save_to_db_cache(symbol, data)

                return data
            else:
                return {
                    "symbol": symbol,
                    "error": "Symbol not found in market data",
                    "cache_hit": False,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "cache_hit": False,
                "timestamp": datetime.now().isoformat(),
            }

    def get_realtime_data_batch_optimized(
        self, symbols: List[str], force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        优化的批量实时数据获取

        优化点:
        1. 只调用一次 ak.stock_zh_a_spot()
        2. 智能缓存管理
        3. 并发处理缓存查询
        4. 批量数据缓存
        """
        result = {}
        symbols_to_fetch = []

        # 并发检查缓存
        if not force_refresh:
            with ThreadPoolExecutor(max_workers=4) as executor:
                cache_futures = {
                    executor.submit(self._get_from_memory_cache, symbol): symbol
                    for symbol in symbols
                }

                for future in as_completed(cache_futures):
                    symbol = cache_futures[future]
                    cached_data = future.result()

                    if cached_data:
                        result[symbol] = cached_data
                    else:
                        symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch = symbols.copy()

        # 批量获取需要更新的数据
        if symbols_to_fetch:
            batch_data = self._fetch_batch_data(symbols_to_fetch)

            # 更新结果和缓存
            for symbol in symbols_to_fetch:
                if symbol in batch_data:
                    data = batch_data[symbol]
                    result[symbol] = data

                    # 异步保存到缓存
                    self._save_to_memory_cache(symbol, data)
                    # 数据库保存可以异步进行
                    threading.Thread(
                        target=self._save_to_db_cache, args=(symbol, data)
                    ).start()
                else:
                    result[symbol] = {
                        "symbol": symbol,
                        "error": "No data available in batch",
                        "cache_hit": False,
                        "timestamp": datetime.now().isoformat(),
                    }

        return result

    def _fetch_batch_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取批量数据 - 只调用一次AKShare API"""
        try:
            if not AKSHARE_AVAILABLE:
                return {symbol: self._get_mock_data(symbol) for symbol in symbols}

            # 检查批量缓存
            now = time.time()
            if (
                self.batch_cache_time
                and now - self.batch_cache_time < self.batch_cache_ttl
                and not self._is_trading_hours()
            ):  # 非交易时间使用批量缓存

                result = {}
                for symbol in symbols:
                    clean_symbol = self._clean_symbol(symbol)
                    if clean_symbol in self.batch_cache:
                        data = self.batch_cache[clean_symbol].copy()
                        data["cache_hit"] = True
                        data["cache_source"] = "batch_cache"
                        result[symbol] = data
                return result

            # 获取全市场数据 (但只调用一次)
            print("📡 获取全市场实时数据...")
            df = ak.stock_zh_a_spot()

            # 更新批量缓存
            self.batch_cache = {}
            self.batch_cache_time = now

            result = {}
            for symbol in symbols:
                clean_symbol = self._clean_symbol(symbol)
                stock_data = df[df["代码"] == clean_symbol]

                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    data = self._convert_akshare_data(symbol, row)
                    data["cache_hit"] = False
                    data["cache_source"] = "network_batch"

                    result[symbol] = data
                    self.batch_cache[clean_symbol] = data.copy()

            return result

        except Exception as e:
            print(f"⚠️ 批量获取失败: {e}")
            return {}

    def _clean_symbol(self, symbol: str) -> str:
        """清理股票代码格式"""
        clean_symbol = symbol
        if "." in clean_symbol:
            clean_symbol = clean_symbol.split(".")[0]
        if clean_symbol.lower().startswith(("sh", "sz")):
            clean_symbol = clean_symbol[2:]
        return clean_symbol

    def _convert_akshare_data(self, symbol: str, row) -> Dict[str, Any]:
        """转换AKShare数据格式"""
        try:
            return {
                "symbol": symbol,
                "name": str(row.get("名称", "N/A")),
                "current_price": float(row.get("最新价", 0)),
                "change": float(row.get("涨跌额", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "open": float(row.get("今开", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": int(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "timestamp": datetime.now().isoformat(),
                "market_status": "open" if self._is_trading_hours() else "closed",
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Data conversion failed: {e}",
                "timestamp": datetime.now().isoformat(),
            }

    def _get_mock_data(self, symbol: str) -> Dict[str, Any]:
        """生成模拟数据"""
        import random

        base_prices = {
            "000001": 10.50,
            "000002": 25.30,
            "600000": 8.20,
            "000858": 158.50,
            "002415": 32.80,
        }

        base_price = base_prices.get(symbol, 50.0)
        change = random.uniform(-2, 2)
        change_percent = (change / base_price) * 100

        return {
            "symbol": symbol,
            "name": f"Mock Stock {symbol}",
            "current_price": round(base_price + change, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "open": round(base_price + random.uniform(-1, 1), 2),
            "high": round(base_price + random.uniform(0, 3), 2),
            "low": round(base_price + random.uniform(-3, 0), 2),
            "volume": random.randint(1000000, 10000000),
            "amount": random.randint(50000000, 500000000),
            "timestamp": datetime.now().isoformat(),
            "market_status": "open" if self._is_trading_hours() else "closed",
            "cache_hit": False,
            "cache_source": "mock",
        }

    def clear_cache(self):
        """清除所有缓存"""
        with self._cache_lock:
            self.memory_cache.clear()
            self.batch_cache.clear()
            self.batch_cache_time = None

        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                self._init_realtime_cache()
            print("✅ 实时数据缓存已清除")
        except Exception as e:
            print(f"⚠️ 清除缓存失败: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._cache_lock:
            memory_count = len(self.memory_cache)
            batch_count = len(self.batch_cache)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM realtime_cache")
            db_count = cursor.fetchone()[0]
            conn.close()
        except:
            db_count = 0

        return {
            "memory_cache_count": memory_count,
            "database_cache_count": db_count,
            "batch_cache_count": batch_count,
            "cache_ttl": self._get_cache_ttl(),
            "is_trading_hours": self._is_trading_hours(),
            "batch_cache_valid": (
                (
                    self.batch_cache_time
                    and time.time() - self.batch_cache_time < self.batch_cache_ttl
                )
                if self.batch_cache_time
                else False
            ),
        }

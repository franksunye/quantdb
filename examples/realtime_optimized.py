"""
优化的实时数据示例 - 展示最佳实践和性能优化技巧

这个示例展示了如何高效地使用 QuantDB 的实时数据功能，
包括缓存策略、批量处理和错误处理。
"""

import qdb
import time
from datetime import datetime
from typing import List, Dict, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class RealtimeDataManager:
    """实时数据管理器 - 优化的实时数据获取和缓存"""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 30  # 缓存30秒
        self.last_batch_fetch = None
        self.batch_data = {}

    def get_cached_or_fetch(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """获取缓存数据或从源获取"""
        now = time.time()

        # 检查缓存
        if not force_refresh and symbol in self.cache:
            cached_time, cached_data = self.cache[symbol]
            if now - cached_time < self.cache_ttl:
                cached_data["cache_hit"] = True
                return cached_data

        # 从源获取
        try:
            data = qdb.get_realtime_data(symbol, force_refresh=force_refresh)
            self.cache[symbol] = (now, data)
            return data
        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "cache_hit": False,
                "timestamp": datetime.now().isoformat(),
            }

    def get_batch_optimized(
        self, symbols: List[str], force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """优化的批量获取 - 使用智能缓存和并发"""
        now = time.time()
        result = {}
        symbols_to_fetch = []

        # 检查哪些需要重新获取
        for symbol in symbols:
            if force_refresh or symbol not in self.cache:
                symbols_to_fetch.append(symbol)
            else:
                cached_time, cached_data = self.cache[symbol]
                if now - cached_time < self.cache_ttl:
                    cached_data["cache_hit"] = True
                    result[symbol] = cached_data
                else:
                    symbols_to_fetch.append(symbol)

        # 批量获取需要更新的数据
        if symbols_to_fetch:
            try:
                # 使用原生批量接口
                batch_data = qdb.get_realtime_data_batch(
                    symbols_to_fetch, force_refresh=force_refresh
                )

                # 更新缓存和结果
                for symbol, data in batch_data.items():
                    self.cache[symbol] = (now, data)
                    result[symbol] = data

            except Exception as e:
                # 如果批量失败，尝试单个获取
                print(f"⚠️ 批量获取失败，尝试单个获取: {e}")
                for symbol in symbols_to_fetch:
                    result[symbol] = self.get_cached_or_fetch(symbol, force_refresh)

        return result


def benchmark_comparison():
    """性能基准测试"""
    print("🔬 性能基准测试")
    print("=" * 50)

    manager = RealtimeDataManager()
    test_symbols = ["000001", "000002", "600000", "000858", "002415"]

    # 测试1: 原生单个请求
    print("\n📊 测试1: 原生单个请求")
    start = time.time()
    for symbol in test_symbols:
        data = qdb.get_realtime_data(symbol)
        print(
            f"  {symbol}: {data.get('current_price', 'N/A')} (缓存: {'是' if data.get('cache_hit') else '否'})"
        )
    time1 = time.time() - start
    print(f"⏱️ 耗时: {time1:.3f}s")

    # 测试2: 原生批量请求
    print("\n📊 测试2: 原生批量请求")
    start = time.time()
    batch_data = qdb.get_realtime_data_batch(test_symbols)
    for symbol, data in batch_data.items():
        print(
            f"  {symbol}: {data.get('current_price', 'N/A')} (缓存: {'是' if data.get('cache_hit') else '否'})"
        )
    time2 = time.time() - start
    print(f"⏱️ 耗时: {time2:.3f}s")

    # 测试3: 优化的批量请求
    print("\n📊 测试3: 优化的批量请求")
    start = time.time()
    optimized_data = manager.get_batch_optimized(test_symbols)
    for symbol, data in optimized_data.items():
        print(
            f"  {symbol}: {data.get('current_price', 'N/A')} (缓存: {'是' if data.get('cache_hit') else '否'})"
        )
    time3 = time.time() - start
    print(f"⏱️ 耗时: {time3:.3f}s")

    # 测试4: 第二次优化批量请求（测试缓存效果）
    print("\n📊 测试4: 第二次优化批量请求（缓存测试）")
    start = time.time()
    cached_data = manager.get_batch_optimized(test_symbols)
    for symbol, data in cached_data.items():
        print(
            f"  {symbol}: {data.get('current_price', 'N/A')} (缓存: {'是' if data.get('cache_hit') else '否'})"
        )
    time4 = time.time() - start
    print(f"⏱️ 耗时: {time4:.3f}s")

    # 性能总结
    print(f"\n📈 性能总结:")
    print(f"  单个请求: {time1:.3f}s")
    print(f"  原生批量: {time2:.3f}s")
    print(f"  优化批量: {time3:.3f}s")
    print(f"  缓存命中: {time4:.3f}s")

    if time1 > 0:
        print(f"  批量 vs 单个: {time1/time2:.2f}x 提升")
        print(f"  优化 vs 原生: {time2/time3:.2f}x 提升")
        print(f"  缓存 vs 网络: {time3/time4:.2f}x 提升")


def concurrent_fetch_demo():
    """并发获取演示"""
    print("\n🚀 并发获取演示")
    print("=" * 50)

    symbols = ["000001", "000002", "600000", "000858", "002415", "300001", "002024"]

    def fetch_single(symbol):
        start = time.time()
        data = qdb.get_realtime_data(symbol)
        duration = time.time() - start
        return symbol, data, duration

    # 串行获取
    print("\n📊 串行获取:")
    start = time.time()
    serial_results = []
    for symbol in symbols:
        symbol, data, duration = fetch_single(symbol)
        serial_results.append((symbol, data, duration))
        print(f"  {symbol}: {duration:.3f}s")
    serial_total = time.time() - start
    print(f"⏱️ 串行总耗时: {serial_total:.3f}s")

    # 并发获取
    print("\n📊 并发获取:")
    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_single, symbol): symbol for symbol in symbols}
        concurrent_results = []

        for future in as_completed(futures):
            symbol, data, duration = future.result()
            concurrent_results.append((symbol, data, duration))
            print(f"  {symbol}: {duration:.3f}s")

    concurrent_total = time.time() - start
    print(f"⏱️ 并发总耗时: {concurrent_total:.3f}s")
    print(f"🚀 并发提升: {serial_total/concurrent_total:.2f}x")


def monitoring_dashboard():
    """监控面板演示"""
    print("\n📺 实时监控面板")
    print("=" * 50)

    manager = RealtimeDataManager()
    watch_list = ["000001", "600000", "000002", "000858"]

    try:
        for round_num in range(3):
            print(f"\n🔄 第 {round_num + 1} 轮 - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)

            start = time.time()
            data = manager.get_batch_optimized(watch_list)
            fetch_time = time.time() - start

            # 显示数据
            for symbol in watch_list:
                if symbol in data:
                    info = data[symbol]
                    if "error" not in info:
                        price = info.get("current_price", info.get("price", 0))
                        change = info.get("change", 0)
                        change_pct = info.get("change_percent", info.get("pct_change", 0))
                        cache_hit = info.get("cache_hit", False)

                        cache_icon = "🚀" if cache_hit else "📡"
                        trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"

                        print(
                            f"  {cache_icon} {symbol}: ¥{price:.2f} {trend_icon}{change:+.2f}({change_pct:+.2f}%)"
                        )
                    else:
                        print(f"  ❌ {symbol}: {info['error']}")
                else:
                    print(f"  ❌ {symbol}: 数据缺失")

            print(f"  ⏱️ 获取耗时: {fetch_time:.3f}s")

            if round_num < 2:
                time.sleep(3)

    except KeyboardInterrupt:
        print("\n⏹️ 监控已停止")


def main():
    """主函数"""
    print("🚀 QuantDB 实时数据优化示例")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 运行各种测试
    benchmark_comparison()
    concurrent_fetch_demo()
    monitoring_dashboard()

    # 缓存统计
    print("\n📊 缓存统计")
    print("=" * 50)
    try:
        stats = qdb.cache_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ 获取缓存统计失败: {e}")


if __name__ == "__main__":
    main()

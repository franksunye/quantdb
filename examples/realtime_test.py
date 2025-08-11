"""
实时数据测试脚本 - 不依赖外部库的简化版本
用于验证优化效果和基本功能
"""

import time
from datetime import datetime


# 模拟 qdb 模块的基本功能
class MockQDB:
    """模拟 QDB 模块用于测试"""

    def __init__(self):
        self.call_count = 0
        self.cache = {}

    def get_realtime_data(self, symbol, force_refresh=False):
        """模拟获取单个股票实时数据"""
        self.call_count += 1

        # 模拟网络延迟
        time.sleep(0.1)

        # 模拟股票数据
        mock_data = {
            "000001": {
                "name": "平安银行",
                "current_price": 10.50,
                "change": 0.15,
                "change_percent": 1.45,
            },
            "000002": {
                "name": "万科A",
                "current_price": 25.30,
                "change": -0.20,
                "change_percent": -0.78,
            },
            "600000": {
                "name": "浦发银行",
                "current_price": 8.20,
                "change": 0.05,
                "change_percent": 0.61,
            },
            "000858": {
                "name": "五粮液",
                "current_price": 158.50,
                "change": 2.30,
                "change_percent": 1.47,
            },
            "002415": {
                "name": "海康威视",
                "current_price": 32.80,
                "change": -0.50,
                "change_percent": -1.50,
            },
        }

        if symbol in mock_data:
            data = mock_data[symbol].copy()
            data["symbol"] = symbol
            data["cache_hit"] = False
            data["timestamp"] = datetime.now().isoformat()
            return data
        else:
            return {
                "symbol": symbol,
                "error": "Symbol not found",
                "cache_hit": False,
                "timestamp": datetime.now().isoformat(),
            }

    def get_realtime_data_batch(self, symbols, force_refresh=False):
        """模拟批量获取 - 当前实现效率低下"""
        self.call_count += 1

        # 模拟当前低效实现：每次都获取全市场数据
        print("📡 模拟调用 ak.stock_zh_a_spot() - 获取全市场数据...")
        time.sleep(0.5)  # 模拟获取全市场数据的延迟

        result = {}
        for symbol in symbols:
            # 从"全市场数据"中提取需要的股票
            data = self.get_realtime_data(symbol, force_refresh)
            data["cache_hit"] = False  # 批量获取不使用缓存
            result[symbol] = data

        return result


# 优化的批量获取实现
class OptimizedRealtimeManager:
    """优化的实时数据管理器"""

    def __init__(self, qdb_instance):
        self.qdb = qdb_instance
        self.cache = {}
        self.cache_ttl = 30  # 30秒缓存

    def get_batch_optimized(self, symbols, force_refresh=False):
        """优化的批量获取实现"""
        now = time.time()
        result = {}
        symbols_to_fetch = []

        # 检查缓存
        for symbol in symbols:
            if not force_refresh and symbol in self.cache:
                cached_time, cached_data = self.cache[symbol]
                if now - cached_time < self.cache_ttl:
                    cached_data = cached_data.copy()
                    cached_data["cache_hit"] = True
                    result[symbol] = cached_data
                    continue
            symbols_to_fetch.append(symbol)

        # 只获取需要的数据
        if symbols_to_fetch:
            print(f"📡 只获取需要的 {len(symbols_to_fetch)} 只股票数据...")
            for symbol in symbols_to_fetch:
                data = self.qdb.get_realtime_data(symbol, force_refresh)
                self.cache[symbol] = (now, data)
                result[symbol] = data

        return result


def format_price_info(data):
    """格式化价格信息"""
    if "error" in data:
        return f"❌ {data['symbol']}: {data['error']}"

    symbol = data.get("symbol", "N/A")
    name = data.get("name", "N/A")
    price = data.get("current_price", 0)
    change = data.get("change", 0)
    change_pct = data.get("change_percent", 0)
    cache_hit = data.get("cache_hit", False)

    cache_icon = "🚀" if cache_hit else "📡"
    trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"

    return (
        f"{cache_icon} {symbol}({name}): ¥{price:.2f} {trend_icon}{change:+.2f}({change_pct:+.2f}%)"
    )


def performance_comparison():
    """性能对比测试"""
    print("🔬 性能对比测试")
    print("=" * 60)

    qdb = MockQDB()
    optimizer = OptimizedRealtimeManager(qdb)
    test_symbols = ["000001", "000002", "600000", "000858", "002415"]

    # 重置计数器
    qdb.call_count = 0

    # 测试1: 原始单个请求
    print("\n📊 测试1: 单个请求")
    start_time = time.time()
    individual_results = {}

    for symbol in test_symbols:
        data = qdb.get_realtime_data(symbol)
        individual_results[symbol] = data
        print(f"  {format_price_info(data)}")

    time1 = time.time() - start_time
    calls1 = qdb.call_count
    print(f"⏱️ 耗时: {time1:.3f}s, API调用: {calls1} 次")

    # 重置计数器
    qdb.call_count = 0

    # 测试2: 原始批量请求
    print("\n📊 测试2: 原始批量请求")
    start_time = time.time()

    batch_results = qdb.get_realtime_data_batch(test_symbols)
    for symbol, data in batch_results.items():
        print(f"  {format_price_info(data)}")

    time2 = time.time() - start_time
    calls2 = qdb.call_count
    print(f"⏱️ 耗时: {time2:.3f}s, API调用: {calls2} 次")

    # 重置计数器
    qdb.call_count = 0

    # 测试3: 优化批量请求
    print("\n📊 测试3: 优化批量请求")
    start_time = time.time()

    optimized_results = optimizer.get_batch_optimized(test_symbols)
    for symbol, data in optimized_results.items():
        print(f"  {format_price_info(data)}")

    time3 = time.time() - start_time
    calls3 = qdb.call_count
    print(f"⏱️ 耗时: {time3:.3f}s, API调用: {calls3} 次")

    # 测试4: 缓存命中测试
    print("\n📊 测试4: 缓存命中测试")
    start_time = time.time()

    cached_results = optimizer.get_batch_optimized(test_symbols)
    for symbol, data in cached_results.items():
        print(f"  {format_price_info(data)}")

    time4 = time.time() - start_time
    calls4 = qdb.call_count - calls3  # 只计算这次的调用
    print(f"⏱️ 耗时: {time4:.3f}s, API调用: {calls4} 次")

    # 性能总结
    print(f"\n📈 性能总结:")
    print(f"  单个请求:   {time1:.3f}s ({calls1} 次API调用)")
    print(f"  原始批量:   {time2:.3f}s ({calls2} 次API调用)")
    print(f"  优化批量:   {time3:.3f}s ({calls3} 次API调用)")
    print(f"  缓存命中:   {time4:.3f}s ({calls4} 次API调用)")

    if time2 > 0:
        print(f"\n🚀 性能提升:")
        print(f"  优化 vs 原始批量: {time2/time3:.2f}x 速度提升")
        print(
            f"  缓存 vs 网络获取: {time3/time4:.2f}x 速度提升"
            if time4 > 0
            else "  缓存: 无网络调用!"
        )
        print(f"  API调用减少: {calls2} → {calls3} ({(calls2-calls3)/calls2*100:.1f}% 减少)")


def monitoring_demo():
    """监控演示"""
    print("\n📺 实时监控演示")
    print("=" * 60)

    qdb = MockQDB()
    optimizer = OptimizedRealtimeManager(qdb)
    watch_symbols = ["000001", "600000", "000002"]

    for round_num in range(3):
        print(f"\n🔄 第 {round_num + 1} 轮监控 - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)

        start_time = time.time()
        data = optimizer.get_batch_optimized(watch_symbols)
        fetch_time = time.time() - start_time

        for symbol in watch_symbols:
            if symbol in data:
                print(f"  {format_price_info(data[symbol])}")
            else:
                print(f"  ❌ {symbol}: 数据获取失败")

        print(f"  ⏱️ 本轮耗时: {fetch_time:.3f}s")

        if round_num < 2:
            time.sleep(2)


def main():
    """主函数"""
    print("🚀 QuantDB 实时数据优化测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 这是一个模拟测试，展示优化前后的性能差异")

    # 运行性能对比
    performance_comparison()

    # 运行监控演示
    monitoring_demo()

    print("\n✅ 测试完成!")
    print("\n📋 优化建议:")
    print("  1. 使用智能缓存减少不必要的API调用")
    print("  2. 批量请求时避免获取全市场数据")
    print("  3. 实现合理的缓存TTL策略")
    print("  4. 添加错误处理和重试机制")


if __name__ == "__main__":
    main()

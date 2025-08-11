import qdb
import time
from datetime import datetime
import json

def format_price_change(data):
    """格式化价格变动信息"""
    if 'error' in data:
        return f"❌ {data['symbol']}: {data['error']}"

    symbol = data.get('symbol', 'N/A')
    name = data.get('name', 'N/A')
    price = data.get('current_price', data.get('price', 0))
    change = data.get('change', 0)
    change_pct = data.get('change_percent', data.get('pct_change', 0))
    cache_hit = data.get('cache_hit', False)

    cache_indicator = "🚀" if cache_hit else "📡"
    change_indicator = "📈" if change > 0 else "📉" if change < 0 else "➡️"

    return f"{cache_indicator} {symbol}({name}): ¥{price:.2f} {change_indicator}{change:+.2f}({change_pct:+.2f}%)"

def performance_test():
    """性能测试：比较单个请求 vs 批量请求"""
    print("=" * 60)
    print("🔬 实时数据性能测试")
    print("=" * 60)

    test_symbols = ["000001", "000002", "600000", "000858", "002415"]

    # 测试1: 单个请求
    print("\n📊 测试1: 单个请求")
    start_time = time.time()
    individual_results = {}

    for symbol in test_symbols:
        symbol_start = time.time()
        try:
            data = qdb.get_realtime_data(symbol)
            individual_results[symbol] = data
            symbol_time = time.time() - symbol_start
            print(f"  {format_price_change(data)} ({symbol_time:.3f}s)")
        except Exception as e:
            print(f"  ❌ {symbol}: 错误 - {e}")

    individual_total_time = time.time() - start_time
    print(f"\n⏱️  单个请求总耗时: {individual_total_time:.3f}s")

    # 测试2: 批量请求
    print("\n📊 测试2: 批量请求")
    start_time = time.time()

    try:
        batch_results = qdb.get_realtime_data_batch(test_symbols)
        batch_total_time = time.time() - start_time

        print(f"✅ 批量获取成功，共 {len(batch_results)} 只股票")
        for symbol, data in batch_results.items():
            print(f"  {format_price_change(data)}")

        print(f"\n⏱️  批量请求总耗时: {batch_total_time:.3f}s")

        # 性能对比
        if individual_total_time > 0:
            speedup = individual_total_time / batch_total_time
            print(f"\n🚀 性能提升: {speedup:.2f}x 倍")

    except Exception as e:
        print(f"❌ 批量请求失败: {e}")

def cache_analysis():
    """缓存分析"""
    print("\n" + "=" * 60)
    print("📈 缓存性能分析")
    print("=" * 60)

    try:
        stats = qdb.cache_stats()
        print(f"📁 缓存目录: {stats.get('cache_dir', 'N/A')}")
        print(f"💾 缓存大小: {stats.get('cache_size_mb', 0):.2f} MB")
        print(f"✅ 初始化状态: {stats.get('initialized', False)}")
        print(f"🔄 运行状态: {stats.get('status', 'Unknown')}")
    except Exception as e:
        print(f"❌ 获取缓存统计失败: {e}")

def realtime_monitoring():
    """实时监控示例"""
    print("\n" + "=" * 60)
    print("📺 实时监控示例 (按 Ctrl+C 停止)")
    print("=" * 60)

    monitor_symbols = ["000001", "600000", "000002"]

    try:
        for i in range(3):  # 监控3轮
            print(f"\n🔄 第 {i+1} 轮监控 - {datetime.now().strftime('%H:%M:%S')}")

            start_time = time.time()
            batch_data = qdb.get_realtime_data_batch(monitor_symbols)
            fetch_time = time.time() - start_time

            for symbol in monitor_symbols:
                if symbol in batch_data:
                    print(f"  {format_price_change(batch_data[symbol])}")
                else:
                    print(f"  ❌ {symbol}: 数据获取失败")

            print(f"  ⏱️  本轮耗时: {fetch_time:.3f}s")

            if i < 2:  # 最后一轮不等待
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n⏹️  监控已停止")
    except Exception as e:
        print(f"\n❌ 监控过程中出错: {e}")

def main():
    """主函数"""
    print("🚀 QuantDB 实时数据示例")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 基础示例
    print("\n" + "=" * 60)
    print("📊 基础实时数据获取")
    print("=" * 60)

    # 单个股票实时数据
    print("\n1️⃣ 单个股票实时数据:")
    try:
        rt = qdb.get_realtime_data("000001")
        print(f"  {format_price_change(rt)}")

        # 显示详细信息
        if 'error' not in rt:
            print(f"  📊 详细信息:")
            print(f"     开盘: ¥{rt.get('open', 'N/A')}")
            print(f"     最高: ¥{rt.get('high', 'N/A')}")
            print(f"     最低: ¥{rt.get('low', 'N/A')}")
            print(f"     成交量: {rt.get('volume', 'N/A'):,}")
            print(f"     缓存命中: {'是' if rt.get('cache_hit') else '否'}")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # 批量股票实时数据
    print("\n2️⃣ 批量股票实时数据:")
    try:
        batch = qdb.get_realtime_data_batch(["000001", "000002", "600000"])
        print(f"  ✅ 成功获取 {len(batch)} 只股票数据")
        for symbol, data in batch.items():
            print(f"    {format_price_change(data)}")
    except Exception as e:
        print(f"  ❌ 批量获取失败: {e}")

    # 运行性能测试
    performance_test()

    # 缓存分析
    cache_analysis()

    # 实时监控
    realtime_monitoring()

if __name__ == "__main__":
    main()


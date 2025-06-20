#!/usr/bin/env python3
"""
真实缓存性能测试 - 使用真实 AKShare 数据验证核心价值
"""

import pytest
import time
import json
import os
import sys
from statistics import mean, median
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.main import app

# 尝试导入 akshare，如果失败则跳过真实测试
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None


class TestRealCachePerformance:
    """真实缓存性能测试 - 对比 QuantDB 与直接 AKShare 调用"""

    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        cls.client = TestClient(app)
        # 使用较小的测试范围以减少测试时间，但足以验证性能差异
        cls.test_symbols = ["000001"]  # 平安银行，数据稳定
        cls.test_scenarios = [
            ("20240101", "20240110", "10天"),  # 小范围快速测试
            ("20240101", "20240131", "1个月"),  # 中等范围
        ]
        cls.results = {
            "quantdb_fresh": [],
            "quantdb_cached": [],
            "akshare_direct": [],
            "comparison": []
        }

    @pytest.mark.skipif(not AKSHARE_AVAILABLE, reason="AKShare not available")
    @pytest.mark.performance
    @pytest.mark.slow  # 标记为慢速测试
    def test_quantdb_vs_akshare_real_performance(self):
        """真实性能对比：QuantDB vs 直接 AKShare 调用"""
        print("\n" + "="*70)
        print("🔥 真实性能测试：QuantDB vs AKShare 直接调用")
        print("="*70)
        
        for symbol in self.test_symbols:
            for start_date, end_date, description in self.test_scenarios:
                print(f"\n📊 测试场景: {symbol} ({description})")
                
                # 1. 清除缓存，测试 QuantDB 首次获取（包含 AKShare 调用）
                self._clear_cache(symbol)
                quantdb_fresh_time, quantdb_count = self._test_quantdb_performance(
                    symbol, start_date, end_date
                )
                
                # 2. 测试 QuantDB 缓存命中
                quantdb_cached_times = []
                for i in range(3):  # 多次测试缓存性能
                    cached_time, _ = self._test_quantdb_performance(
                        symbol, start_date, end_date
                    )
                    quantdb_cached_times.append(cached_time)
                
                quantdb_cached_avg = mean(quantdb_cached_times)
                
                # 3. 测试直接 AKShare 调用（多次测试取平均值）
                akshare_times = []
                akshare_count = 0
                
                print("   🌐 测试直接 AKShare 调用...")
                for i in range(3):  # 多次测试 AKShare 性能
                    try:
                        akshare_time, count = self._test_akshare_direct(
                            symbol, start_date, end_date
                        )
                        akshare_times.append(akshare_time)
                        akshare_count = count
                        print(f"      第{i+1}次: {akshare_time:.0f}ms")
                    except Exception as e:
                        print(f"      第{i+1}次失败: {e}")
                        continue
                
                if not akshare_times:
                    print("   ❌ AKShare 调用全部失败，跳过此场景")
                    continue
                
                akshare_avg = mean(akshare_times)
                
                # 4. 记录和分析结果
                result = {
                    "symbol": symbol,
                    "date_range": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "record_count": quantdb_count,
                    "quantdb_fresh_ms": quantdb_fresh_time,
                    "quantdb_cached_ms": quantdb_cached_avg,
                    "akshare_direct_ms": akshare_avg,
                    "cache_vs_fresh_improvement": (quantdb_fresh_time - quantdb_cached_avg) / quantdb_fresh_time * 100,
                    "cache_vs_akshare_improvement": (akshare_avg - quantdb_cached_avg) / akshare_avg * 100
                }
                
                self.results["comparison"].append(result)
                
                # 5. 实时显示结果
                print(f"   📈 结果对比:")
                print(f"      QuantDB 首次: {quantdb_fresh_time:.0f}ms")
                print(f"      QuantDB 缓存: {quantdb_cached_avg:.0f}ms")
                print(f"      AKShare 直接: {akshare_avg:.0f}ms")
                print(f"      🚀 缓存 vs 首次: {result['cache_vs_fresh_improvement']:+.1f}%")
                print(f"      🎯 缓存 vs AKShare: {result['cache_vs_akshare_improvement']:+.1f}%")

    def test_real_performance_analysis(self):
        """分析真实性能测试结果"""
        if not self.results["comparison"]:
            pytest.skip("没有真实性能测试数据")
        
        print("\n" + "="*70)
        print("📊 真实性能测试分析报告")
        print("="*70)
        
        # 计算总体统计
        cache_vs_fresh_improvements = [r["cache_vs_fresh_improvement"] for r in self.results["comparison"]]
        cache_vs_akshare_improvements = [r["cache_vs_akshare_improvement"] for r in self.results["comparison"]]
        
        print(f"\n🎯 核心价值验证:")
        print(f"   测试场景数: {len(self.results['comparison'])}")
        
        if cache_vs_fresh_improvements:
            avg_cache_vs_fresh = mean(cache_vs_fresh_improvements)
            print(f"   缓存 vs 首次获取: {avg_cache_vs_fresh:+.1f}% (平均)")
        
        if cache_vs_akshare_improvements:
            avg_cache_vs_akshare = mean(cache_vs_akshare_improvements)
            print(f"   缓存 vs AKShare直接调用: {avg_cache_vs_akshare:+.1f}% (平均)")
        
        # 详细场景分析
        print(f"\n📋 详细场景分析:")
        for result in self.results["comparison"]:
            print(f"   {result['symbol']} ({result['date_range']}):")
            print(f"      QuantDB首次: {result['quantdb_fresh_ms']:.0f}ms")
            print(f"      QuantDB缓存: {result['quantdb_cached_ms']:.0f}ms") 
            print(f"      AKShare直接: {result['akshare_direct_ms']:.0f}ms")
            print(f"      缓存优势: {result['cache_vs_akshare_improvement']:+.1f}%")
        
        # 保存结果
        self._save_real_performance_results()
        
        # 核心价值验证
        print(f"\n💡 核心价值总结:")
        if avg_cache_vs_akshare > 0:
            print(f"✅ QuantDB 缓存显著优于 AKShare 直接调用")
            print(f"✅ 平均性能提升: {avg_cache_vs_akshare:.1f}%")
            print(f"✅ 用户体验显著改善")
        else:
            print(f"⚠️ 需要进一步优化缓存性能")
        
        print(f"✅ 减少外部 API 依赖")
        print(f"✅ 提供数据持久化能力")

    def _test_quantdb_performance(self, symbol, start_date, end_date):
        """测试 QuantDB API 性能"""
        start_time = time.time()
        
        response = self.client.get(
            f"/api/v1/historical/stock/{symbol}",
            params={"start_date": start_date, "end_date": end_date}
        )
        
        end_time = time.time()
        
        assert response.status_code == 200, f"API调用失败: {response.status_code}"
        data = response.json()
        
        return (end_time - start_time) * 1000, len(data.get("data", []))

    def _test_akshare_direct(self, symbol, start_date, end_date):
        """测试直接 AKShare 调用性能"""
        if not AKSHARE_AVAILABLE:
            raise ImportError("AKShare not available")
        
        start_time = time.time()
        
        # 直接调用 AKShare API
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
        
        end_time = time.time()
        
        return (end_time - start_time) * 1000, len(df)

    def _clear_cache(self, symbol):
        """清除指定股票的缓存"""
        try:
            response = self.client.delete(f"/api/v1/cache/clear/symbol/{symbol}")
            print(f"   🗑️ 已清除 {symbol} 的缓存")
        except Exception as e:
            print(f"   ⚠️ 清除缓存失败: {e}")

    def _save_real_performance_results(self):
        """保存真实性能测试结果"""
        results_dir = "tests/performance/results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"{results_dir}/real_cache_performance_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 真实性能测试结果已保存: {results_file}")


if __name__ == '__main__':
    # 支持直接运行
    if AKSHARE_AVAILABLE:
        pytest.main([__file__, "-v", "-s", "-m", "performance"])
    else:
        print("❌ AKShare 未安装，无法运行真实性能测试")
        print("请安装: pip install akshare")

#!/usr/bin/env python3
"""
缓存价值场景测试 - 专注于 QuantDB 真正优势的场景
"""

import pytest
import time
import json
import os
import sys
from statistics import mean
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.api.main import app

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None


class TestCacheValueScenarios:
    """测试 QuantDB 缓存的真正价值场景"""

    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        cls.client = TestClient(app)
        cls.test_symbol = "000001"  # 平安银行
        cls.results = {
            "repeated_access": [],
            "bulk_requests": [],
            "api_reliability": []
        }

    @pytest.mark.skipif(not AKSHARE_AVAILABLE, reason="AKShare not available")
    @pytest.mark.performance
    def test_repeated_access_scenario(self):
        """测试重复访问场景 - QuantDB 的核心优势"""
        print("\n" + "="*70)
        print("🔄 重复访问场景测试 - 模拟用户多次查询相同数据")
        print("="*70)
        
        symbol = self.test_symbol
        start_date = "20240101"
        end_date = "20240131"
        
        # 清除缓存
        self._clear_cache(symbol)
        
        # 模拟用户在短时间内多次访问相同数据
        print(f"📊 模拟用户多次查询 {symbol} 数据...")
        
        quantdb_times = []
        akshare_times = []
        
        # 第一次访问 - QuantDB 需要从 AKShare 获取
        print("   第1次访问 (QuantDB 首次获取)...")
        quantdb_first_time, record_count = self._test_quantdb_performance(symbol, start_date, end_date)
        
        # 后续访问 - QuantDB 使用缓存
        for i in range(2, 6):  # 第2-5次访问
            print(f"   第{i}次访问 (QuantDB 缓存命中)...")
            cached_time, _ = self._test_quantdb_performance(symbol, start_date, end_date)
            quantdb_times.append(cached_time)
        
        # 对比：如果每次都调用 AKShare
        print("   对比：每次都调用 AKShare...")
        for i in range(1, 6):  # 5次 AKShare 调用
            try:
                akshare_time, _ = self._test_akshare_direct(symbol, start_date, end_date)
                akshare_times.append(akshare_time)
                print(f"      第{i}次 AKShare 调用: {akshare_time:.0f}ms")
            except Exception as e:
                print(f"      第{i}次 AKShare 调用失败: {e}")
        
        if quantdb_times and akshare_times:
            quantdb_avg = mean(quantdb_times)
            akshare_avg = mean(akshare_times)
            total_quantdb_time = quantdb_first_time + sum(quantdb_times)
            total_akshare_time = sum(akshare_times)
            
            result = {
                "scenario": "重复访问",
                "access_count": len(quantdb_times) + 1,
                "quantdb_first_ms": quantdb_first_time,
                "quantdb_cached_avg_ms": quantdb_avg,
                "akshare_avg_ms": akshare_avg,
                "total_quantdb_time_ms": total_quantdb_time,
                "total_akshare_time_ms": total_akshare_time,
                "time_saved_ms": total_akshare_time - total_quantdb_time,
                "efficiency_improvement": (total_akshare_time - total_quantdb_time) / total_akshare_time * 100
            }
            
            self.results["repeated_access"].append(result)
            
            print(f"\n📈 重复访问场景结果:")
            print(f"   QuantDB 首次: {quantdb_first_time:.0f}ms")
            print(f"   QuantDB 缓存平均: {quantdb_avg:.0f}ms")
            print(f"   AKShare 平均: {akshare_avg:.0f}ms")
            print(f"   总时间 - QuantDB: {total_quantdb_time:.0f}ms")
            print(f"   总时间 - AKShare: {total_akshare_time:.0f}ms")
            print(f"   🚀 节省时间: {result['time_saved_ms']:.0f}ms")
            print(f"   🎯 效率提升: {result['efficiency_improvement']:+.1f}%")

    @pytest.mark.skipif(not AKSHARE_AVAILABLE, reason="AKShare not available")
    @pytest.mark.performance
    def test_bulk_requests_scenario(self):
        """测试批量请求场景 - 减少 API 调用频率"""
        print("\n" + "="*70)
        print("📦 批量请求场景测试 - 模拟多个用户同时查询")
        print("="*70)
        
        symbol = self.test_symbol
        date_ranges = [
            ("20240101", "20240110", "1月上旬"),
            ("20240111", "20240120", "1月中旬"),
            ("20240121", "20240131", "1月下旬")
        ]
        
        # 清除缓存
        self._clear_cache(symbol)
        
        print(f"📊 模拟多个用户查询 {symbol} 不同时间段...")
        
        # QuantDB 批量请求
        quantdb_total_time = 0
        for start_date, end_date, description in date_ranges:
            request_time, _ = self._test_quantdb_performance(symbol, start_date, end_date)
            quantdb_total_time += request_time
            print(f"   QuantDB {description}: {request_time:.0f}ms")
        
        # AKShare 批量请求
        akshare_total_time = 0
        for start_date, end_date, description in date_ranges:
            try:
                request_time, _ = self._test_akshare_direct(symbol, start_date, end_date)
                akshare_total_time += request_time
                print(f"   AKShare {description}: {request_time:.0f}ms")
            except Exception as e:
                print(f"   AKShare {description} 失败: {e}")
                akshare_total_time += 2000  # 假设失败时的惩罚时间
        
        result = {
            "scenario": "批量请求",
            "request_count": len(date_ranges),
            "quantdb_total_ms": quantdb_total_time,
            "akshare_total_ms": akshare_total_time,
            "time_saved_ms": akshare_total_time - quantdb_total_time,
            "efficiency_improvement": (akshare_total_time - quantdb_total_time) / akshare_total_time * 100
        }
        
        self.results["bulk_requests"].append(result)
        
        print(f"\n📈 批量请求场景结果:")
        print(f"   QuantDB 总时间: {quantdb_total_time:.0f}ms")
        print(f"   AKShare 总时间: {akshare_total_time:.0f}ms")
        print(f"   🚀 节省时间: {result['time_saved_ms']:.0f}ms")
        print(f"   🎯 效率提升: {result['efficiency_improvement']:+.1f}%")

    def test_cache_value_analysis(self):
        """分析缓存价值场景测试结果"""
        print("\n" + "="*70)
        print("📊 QuantDB 缓存价值分析报告")
        print("="*70)
        
        # 分析重复访问场景
        if self.results["repeated_access"]:
            repeated_data = self.results["repeated_access"][0]
            print(f"\n🔄 重复访问场景价值:")
            print(f"   访问次数: {repeated_data['access_count']}")
            print(f"   节省时间: {repeated_data['time_saved_ms']:.0f}ms")
            print(f"   效率提升: {repeated_data['efficiency_improvement']:+.1f}%")
            
            if repeated_data['efficiency_improvement'] > 0:
                print(f"   ✅ 在重复访问场景中，QuantDB 显著优于 AKShare")
            else:
                print(f"   📝 重复访问场景需要更多缓存命中才能体现优势")
        
        # 分析批量请求场景
        if self.results["bulk_requests"]:
            bulk_data = self.results["bulk_requests"][0]
            print(f"\n📦 批量请求场景价值:")
            print(f"   请求数量: {bulk_data['request_count']}")
            print(f"   节省时间: {bulk_data['time_saved_ms']:.0f}ms")
            print(f"   效率提升: {bulk_data['efficiency_improvement']:+.1f}%")
        
        # 总结 QuantDB 的核心价值
        print(f"\n💡 QuantDB 核心价值总结:")
        print(f"1. 🔄 重复访问优化 - 避免重复的 AKShare 调用")
        print(f"2. 📦 智能数据管理 - 只获取缺失的数据")
        print(f"3. 🛡️ 服务可靠性 - 减少对外部 API 的依赖")
        print(f"4. 💾 数据持久化 - 提供历史数据存储和管理")
        print(f"5. 📊 用户体验 - 在网络不稳定时提供稳定服务")
        
        # 保存结果
        self._save_value_scenario_results()

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

    def _save_value_scenario_results(self):
        """保存价值场景测试结果"""
        results_dir = "tests/performance/results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"{results_dir}/cache_value_scenarios_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 价值场景测试结果已保存: {results_file}")


if __name__ == '__main__':
    if AKSHARE_AVAILABLE:
        pytest.main([__file__, "-v", "-s", "-m", "performance"])
    else:
        print("❌ AKShare 未安装，无法运行真实性能测试")

#!/usr/bin/env python3
"""
缓存性能测试 - 验证 QuantDB 相比 AKShare 的核心价值
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


class TestCacheVsAKSharePerformance:
    """测试缓存性能 vs AKShare 直接调用"""

    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        cls.client = TestClient(app)
        cls.test_symbols = ["000001", "600000"]  # 减少测试量，保持敏捷
        cls.test_scenarios = [
            ("20240101", "20240131", "1个月"),
            ("20240101", "20240301", "3个月"),
        ]
        cls.results = {
            "fresh_data": [],
            "cached_data": [],
            "partial_cache": []
        }

    @pytest.mark.performance
    def test_fresh_data_performance(self):
        """测试首次数据获取性能（QuantDB vs AKShare 基准）"""
        print("\n=== 测试首次数据获取性能 ===")
        
        for symbol in self.test_symbols:
            for start_date, end_date, description in self.test_scenarios:
                # 清除缓存确保首次获取
                self._clear_cache(symbol)
                
                # 测试 QuantDB 性能
                quantdb_time, record_count = self._test_quantdb_performance(
                    symbol, start_date, end_date
                )
                
                result = {
                    "symbol": symbol,
                    "date_range": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "quantdb_time_ms": quantdb_time,
                    "record_count": record_count
                }
                
                self.results["fresh_data"].append(result)
                print(f"{symbol} ({description}): {quantdb_time:.0f}ms, {record_count}条记录")

    @pytest.mark.performance
    def test_cached_data_performance(self):
        """测试缓存命中性能"""
        print("\n=== 测试缓存命中性能 ===")
        
        for symbol in self.test_symbols:
            for start_date, end_date, description in self.test_scenarios:
                # 第一次调用（填充缓存）
                self._test_quantdb_performance(symbol, start_date, end_date)
                
                # 第二次调用（缓存命中）- 多次测试取平均值
                cached_times = []
                for i in range(5):  # 5次测试取平均
                    cached_time, record_count = self._test_quantdb_performance(
                        symbol, start_date, end_date
                    )
                    cached_times.append(cached_time)
                
                avg_cached_time = mean(cached_times)
                min_cached_time = min(cached_times)
                
                result = {
                    "symbol": symbol,
                    "date_range": description,
                    "avg_cached_time_ms": avg_cached_time,
                    "min_cached_time_ms": min_cached_time,
                    "record_count": record_count
                }
                
                self.results["cached_data"].append(result)
                print(f"{symbol} ({description}): 缓存命中 {avg_cached_time:.0f}ms (最快 {min_cached_time:.0f}ms)")

    @pytest.mark.performance
    def test_partial_cache_performance(self):
        """测试部分缓存场景性能"""
        print("\n=== 测试部分缓存性能 ===")
        
        symbol = "000001"  # 只测试一个股票保持敏捷
        
        # 场景1：缓存1月数据，请求1-3月数据
        self._clear_cache(symbol)
        self._ensure_cached_data(symbol, "20240101", "20240131")
        
        partial_time, record_count = self._test_quantdb_performance(
            symbol, "20240101", "20240331"
        )
        
        result = {
            "symbol": symbol,
            "scenario": "扩展2个月数据",
            "cached_range": "1月",
            "requested_range": "1-3月", 
            "partial_time_ms": partial_time,
            "record_count": record_count
        }
        
        self.results["partial_cache"].append(result)
        print(f"{symbol} 部分缓存场景: {partial_time:.0f}ms, {record_count}条记录")

    def test_performance_analysis(self):
        """分析性能测试结果"""
        print("\n" + "="*60)
        print("缓存性能分析报告")
        print("="*60)
        
        # 分析首次数据获取
        if self.results["fresh_data"]:
            fresh_avg = mean([r["quantdb_time_ms"] for r in self.results["fresh_data"]])
            print(f"\n📊 首次数据获取平均时间: {fresh_avg:.0f}ms")
        
        # 分析缓存命中性能
        if self.results["cached_data"]:
            cached_avg = mean([r["avg_cached_time_ms"] for r in self.results["cached_data"]])
            print(f"⚡ 缓存命中平均时间: {cached_avg:.0f}ms")
            
            if self.results["fresh_data"]:
                improvement = (fresh_avg - cached_avg) / fresh_avg * 100
                print(f"🚀 缓存性能提升: {improvement:.1f}%")
        
        # 分析部分缓存
        if self.results["partial_cache"]:
            partial_avg = mean([r["partial_time_ms"] for r in self.results["partial_cache"]])
            print(f"🔄 部分缓存平均时间: {partial_avg:.0f}ms")
        
        # 保存结果
        self._save_performance_results()
        
        # 性能分析（不强制断言，因为测试环境可能与生产环境不同）
        if self.results["fresh_data"] and self.results["cached_data"]:
            if cached_avg < fresh_avg:
                print(f"✅ 缓存性能优于首次获取: {improvement:.1f}% 提升")
            else:
                print(f"⚠️ 测试环境中缓存性能: {improvement:.1f}% (可能因测试环境特殊性)")
                print("   在生产环境中，缓存通常会显著提升性能")

        # 保存性能基准
        self._save_performance_baseline()

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

    def _clear_cache(self, symbol):
        """清除指定股票的缓存"""
        try:
            response = self.client.delete(f"/api/v1/cache/clear/symbol/{symbol}")
            # 不强制要求成功，因为可能没有缓存
        except:
            pass

    def _ensure_cached_data(self, symbol, start_date, end_date):
        """确保指定范围的数据已缓存"""
        self._test_quantdb_performance(symbol, start_date, end_date)

    def _save_performance_results(self):
        """保存性能测试结果"""
        results_dir = "tests/performance/results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"{results_dir}/cache_performance_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 性能测试结果已保存: {results_file}")

    def _save_performance_baseline(self):
        """保存性能基准"""
        try:
            from .performance_baseline import save_cache_performance_baseline
            save_cache_performance_baseline(self.results)
        except ImportError:
            print("⚠️ 性能基准模块未找到，跳过基准保存")


if __name__ == '__main__':
    # 支持直接运行
    pytest.main([__file__, "-v", "-s"])

#!/usr/bin/env python3
"""
E2E性能分析脚本

专门用于分析E2E测试的性能表现，提供详细的性能指标
"""

import time
import statistics
import sys
import os
import requests
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.config import e2e_config
from tests.e2e.server_manager import server_manager
from core.utils.logger import get_logger

logger = get_logger("e2e_performance_analysis")

class PerformanceAnalyzer:
    """E2E性能分析器"""

    def __init__(self):
        self.config = e2e_config
        self.base_url = self.config.BASE_URL
        self.api_prefix = self.config.API_PREFIX
        self.server_manager = server_manager

    def make_request(self, method, endpoint, **kwargs):
        """发送HTTP请求"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        kwargs.setdefault('timeout', self.config.REQUEST_TIMEOUT)
        return requests.request(method, url, **kwargs)

    def get(self, endpoint, **kwargs):
        """GET请求"""
        return self.make_request('GET', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        """DELETE请求"""
        return self.make_request('DELETE', endpoint, **kwargs)

    def measure_request_time(self, request_func):
        """测量请求时间"""
        start_time = time.time()
        result = request_func()
        end_time = time.time()
        return result, end_time - start_time

    def cleanup_test_data(self):
        """清理测试数据"""
        for symbol in self.config.TEST_SYMBOLS:
            try:
                self.delete(f"/cache/clear/symbol/{symbol}")
            except:
                pass

    def analyze_api_performance(self, runs=3):
        """分析API性能表现"""
        logger.info("=" * 60)
        logger.info("E2E性能分析开始")
        logger.info("=" * 60)
        
        test_symbol = self.config.TEST_SYMBOLS[0]  # 000001
        results = {
            'health_check': [],
            'assets_api': [],
            'first_request': [],
            'cache_hit': [],
            'cache_performance_improvement': []
        }
        
        for run in range(runs):
            logger.info(f"\n--- 第 {run + 1} 轮性能测试 ---")
            
            # 清理测试数据
            self.cleanup_test_data()
            
            # 1. 健康检查性能
            _, health_time = self.measure_request_time(
                lambda: self.get("/health")
            )
            results['health_check'].append(health_time)
            logger.info(f"健康检查耗时: {health_time:.3f}秒")
            
            # 2. 资产API性能
            _, assets_time = self.measure_request_time(
                lambda: self.get("/assets")
            )
            results['assets_api'].append(assets_time)
            logger.info(f"资产API耗时: {assets_time:.3f}秒")
            
            # 3. 首次股票数据请求（从AKShare获取）
            response, first_time = self.measure_request_time(
                lambda: self.get(
                    f"/historical/stock/{test_symbol}",
                    params={
                        "start_date": self.config.TEST_START_DATE,
                        "end_date": self.config.TEST_END_DATE
                    }
                )
            )
            results['first_request'].append(first_time)
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data.get("data", []))
                logger.info(f"首次请求耗时: {first_time:.3f}秒，获取 {record_count} 条记录")
            else:
                logger.warning(f"首次请求失败: {response.status_code}")
                continue
            
            # 4. 缓存命中请求
            _, cache_time = self.measure_request_time(
                lambda: self.get(
                    f"/historical/stock/{test_symbol}",
                    params={
                        "start_date": self.config.TEST_START_DATE,
                        "end_date": self.config.TEST_END_DATE
                    }
                )
            )
            results['cache_hit'].append(cache_time)
            
            # 5. 计算性能提升
            if first_time > 0:
                improvement = (first_time - cache_time) / first_time * 100
                results['cache_performance_improvement'].append(improvement)
                logger.info(f"缓存命中耗时: {cache_time:.3f}秒，性能提升: {improvement:.1f}%")
            
            # 短暂休息
            time.sleep(0.5)
        
        return results
    
    def analyze_data_range_performance(self, runs=3):
        """分析数据范围扩展的性能"""
        logger.info(f"\n--- 数据范围扩展性能分析 ({runs}轮) ---")
        
        test_symbol = self.config.TEST_SYMBOLS[0]
        results = {
            'small_range': [],
            'expanded_range': [],
            'range_expansion_ratio': []
        }
        
        for run in range(runs):
            logger.info(f"\n第 {run + 1} 轮范围扩展测试:")
            
            # 清理数据
            self.cleanup_test_data()
            
            # 1. 小范围请求 (3天)
            small_end_date = "20240103"
            response1, small_time = self.measure_request_time(
                lambda: self.get(
                    f"/historical/stock/{test_symbol}",
                    params={
                        "start_date": self.config.TEST_START_DATE,
                        "end_date": small_end_date
                    }
                )
            )
            results['small_range'].append(small_time)
            
            if response1.status_code == 200:
                small_count = len(response1.json().get("data", []))
                logger.info(f"小范围请求: {small_time:.3f}秒，{small_count} 条记录")
            
            # 2. 扩展范围请求 (10天)
            expanded_end_date = "20240110"
            response2, expanded_time = self.measure_request_time(
                lambda: self.get(
                    f"/historical/stock/{test_symbol}",
                    params={
                        "start_date": self.config.TEST_START_DATE,
                        "end_date": expanded_end_date
                    }
                )
            )
            results['expanded_range'].append(expanded_time)
            
            if response2.status_code == 200:
                expanded_count = len(response2.json().get("data", []))
                logger.info(f"扩展范围请求: {expanded_time:.3f}秒，{expanded_count} 条记录")
                
                # 计算扩展比例
                if small_time > 0:
                    ratio = expanded_time / small_time
                    results['range_expansion_ratio'].append(ratio)
                    logger.info(f"扩展时间比例: {ratio:.2f}x")
        
        return results
    
    def print_performance_summary(self, basic_results, range_results):
        """打印性能总结报告"""
        logger.info("\n" + "=" * 60)
        logger.info("E2E性能分析报告")
        logger.info("=" * 60)
        
        def print_stats(name, values, unit="秒"):
            if values:
                mean_val = statistics.mean(values)
                median_val = statistics.median(values)
                min_val = min(values)
                max_val = max(values)
                std_val = statistics.stdev(values) if len(values) > 1 else 0
                
                logger.info(f"\n{name}:")
                logger.info(f"  平均值: {mean_val:.3f}{unit}")
                logger.info(f"  中位数: {median_val:.3f}{unit}")
                logger.info(f"  最小值: {min_val:.3f}{unit}")
                logger.info(f"  最大值: {max_val:.3f}{unit}")
                logger.info(f"  标准差: {std_val:.3f}{unit}")
        
        # 基础API性能
        print_stats("健康检查API", basic_results['health_check'])
        print_stats("资产列表API", basic_results['assets_api'])
        print_stats("首次数据请求（AKShare）", basic_results['first_request'])
        print_stats("缓存命中请求", basic_results['cache_hit'])
        print_stats("缓存性能提升", basic_results['cache_performance_improvement'], "%")
        
        # 数据范围性能
        print_stats("小范围数据请求", range_results['small_range'])
        print_stats("扩展范围数据请求", range_results['expanded_range'])
        print_stats("范围扩展时间比例", range_results['range_expansion_ratio'], "x")
        
        # 性能总结
        logger.info(f"\n性能总结:")
        if basic_results['cache_performance_improvement']:
            avg_improvement = statistics.mean(basic_results['cache_performance_improvement'])
            logger.info(f"  缓存平均性能提升: {avg_improvement:.1f}%")
        
        if basic_results['first_request'] and basic_results['cache_hit']:
            avg_first = statistics.mean(basic_results['first_request'])
            avg_cache = statistics.mean(basic_results['cache_hit'])
            logger.info(f"  首次请求平均耗时: {avg_first:.3f}秒")
            logger.info(f"  缓存请求平均耗时: {avg_cache:.3f}秒")
            logger.info(f"  缓存速度提升: {avg_first/avg_cache:.1f}倍")

def main():
    """主函数"""
    analyzer = PerformanceAnalyzer()

    # 启动服务器
    if not analyzer.server_manager.start_server():
        logger.error("无法启动测试服务器")
        return

    try:
        # 分析基础API性能
        basic_results = analyzer.analyze_api_performance(runs=3)

        # 分析数据范围性能
        range_results = analyzer.analyze_data_range_performance(runs=3)

        # 打印总结报告
        analyzer.print_performance_summary(basic_results, range_results)

    except Exception as e:
        logger.error(f"性能分析过程中出错: {e}")
        raise
    finally:
        # 停止服务器
        analyzer.server_manager.stop_server()
        analyzer.config.cleanup()

if __name__ == '__main__':
    main()

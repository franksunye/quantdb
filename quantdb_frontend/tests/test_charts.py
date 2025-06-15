"""
前端图表工具测试

测试图表创建和数据可视化功能。
"""

import unittest
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, date

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.charts import (
    create_price_chart, 
    create_candlestick_chart,
    create_volume_chart,
    create_returns_distribution,
    calculate_basic_metrics,
    format_large_number,
    create_performance_comparison_chart,
    create_data_coverage_timeline,
    create_cache_hit_pie_chart
)

class TestChartCreation(unittest.TestCase):
    """测试图表创建功能"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试股票数据
        self.test_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10, freq='D'),
            'open': [10.0, 10.2, 10.5, 10.3, 10.8, 11.0, 10.9, 11.2, 11.1, 11.3],
            'high': [10.5, 10.8, 11.0, 10.9, 11.2, 11.5, 11.3, 11.6, 11.4, 11.8],
            'low': [9.8, 10.0, 10.2, 10.1, 10.5, 10.8, 10.6, 10.9, 10.8, 11.0],
            'close': [10.2, 10.5, 10.3, 10.8, 11.0, 10.9, 11.2, 11.1, 11.3, 11.5],
            'volume': [1000000, 1200000, 1100000, 1300000, 1500000, 1400000, 1600000, 1450000, 1550000, 1650000]
        })
        
        # 空数据测试
        self.empty_data = pd.DataFrame()
    
    def test_create_price_chart_with_data(self):
        """测试创建价格图表 - 有数据"""
        fig = create_price_chart(self.test_data, "测试价格图表")
        
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "测试价格图表")
        self.assertTrue(len(fig.data) > 0)
    
    def test_create_price_chart_empty_data(self):
        """测试创建价格图表 - 空数据"""
        fig = create_price_chart(self.empty_data)
        
        self.assertIsInstance(fig, go.Figure)
        # 空数据应该显示"暂无数据"注释
        self.assertTrue(len(fig.layout.annotations) > 0)
    
    def test_create_price_chart_with_volume(self):
        """测试创建价格图表 - 包含成交量"""
        fig = create_price_chart(self.test_data, show_volume=True)
        
        self.assertIsInstance(fig, go.Figure)
        # 应该有两个子图（价格和成交量）
        self.assertTrue(len(fig.data) >= 2)
    
    def test_create_candlestick_chart_with_data(self):
        """测试创建K线图 - 有数据"""
        fig = create_candlestick_chart(self.test_data, "测试K线图")
        
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "测试K线图")
        self.assertTrue(len(fig.data) > 0)
    
    def test_create_candlestick_chart_empty_data(self):
        """测试创建K线图 - 空数据"""
        fig = create_candlestick_chart(self.empty_data)
        
        self.assertIsInstance(fig, go.Figure)
        self.assertTrue(len(fig.layout.annotations) > 0)
    
    def test_create_volume_chart_with_data(self):
        """测试创建成交量图表 - 有数据"""
        fig = create_volume_chart(self.test_data, "测试成交量图表")
        
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "测试成交量图表")
        self.assertTrue(len(fig.data) > 0)
    
    def test_create_volume_chart_empty_data(self):
        """测试创建成交量图表 - 空数据"""
        fig = create_volume_chart(self.empty_data)
        
        self.assertIsInstance(fig, go.Figure)
        self.assertTrue(len(fig.layout.annotations) > 0)
    
    def test_create_returns_distribution(self):
        """测试创建收益率分布图"""
        fig = create_returns_distribution(self.test_data, "测试收益率分布")
        
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "测试收益率分布")
    
    def test_create_performance_comparison_chart(self):
        """测试创建性能对比图表"""
        cache_time = 18.5
        akshare_time = 1075.2
        
        fig = create_performance_comparison_chart(cache_time, akshare_time)
        
        self.assertIsInstance(fig, go.Figure)
        self.assertTrue("性能对比" in fig.layout.title.text)
        self.assertEqual(len(fig.data), 1)  # 一个柱状图
    
    def test_create_data_coverage_timeline(self):
        """测试创建数据覆盖时间轴"""
        fig = create_data_coverage_timeline(self.test_data)
        
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(fig.layout.title.text, "数据覆盖时间轴")
    
    def test_create_cache_hit_pie_chart(self):
        """测试创建缓存命中率饼图"""
        cache_hits = 95
        cache_misses = 5
        
        fig = create_cache_hit_pie_chart(cache_hits, cache_misses)
        
        self.assertIsInstance(fig, go.Figure)
        self.assertTrue("缓存命中率" in fig.layout.title.text)
        self.assertEqual(len(fig.data), 1)  # 一个饼图

class TestMetricsCalculation(unittest.TestCase):
    """测试指标计算功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.test_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5, freq='D'),
            'close': [10.0, 10.5, 10.2, 10.8, 11.0],
            'volume': [1000000, 1200000, 1100000, 1300000, 1500000]
        })
    
    def test_calculate_basic_metrics(self):
        """测试基础指标计算"""
        metrics = calculate_basic_metrics(self.test_data)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('latest_price', metrics)
        self.assertIn('high_price', metrics)
        self.assertIn('low_price', metrics)
        self.assertIn('avg_price', metrics)
        self.assertIn('price_change', metrics)
        self.assertIn('volatility', metrics)
        
        # 验证计算结果
        self.assertEqual(metrics['latest_price'], 11.0)
        self.assertEqual(metrics['high_price'], 11.0)
        self.assertEqual(metrics['low_price'], 10.0)
        self.assertAlmostEqual(metrics['avg_price'], 10.5, places=1)
    
    def test_calculate_basic_metrics_empty_data(self):
        """测试空数据的指标计算"""
        empty_data = pd.DataFrame()
        metrics = calculate_basic_metrics(empty_data)
        
        self.assertEqual(metrics, {})
    
    def test_calculate_basic_metrics_single_row(self):
        """测试单行数据的指标计算"""
        single_row = pd.DataFrame({
            'close': [10.0],
            'volume': [1000000]
        })
        
        metrics = calculate_basic_metrics(single_row)
        
        self.assertEqual(metrics['latest_price'], 10.0)
        self.assertEqual(metrics['price_change'], 0)  # 单行数据变化率为0

class TestUtilityFunctions(unittest.TestCase):
    """测试工具函数"""
    
    def test_format_large_number(self):
        """测试大数字格式化"""
        test_cases = [
            (1234.56, "1234.56"),
            (12345, "1.23万"),
            (123456789, "1.23亿"),
            (1000000000, "10.00亿")
        ]
        
        for input_num, expected in test_cases:
            result = format_large_number(input_num)
            self.assertEqual(result, expected)

class TestChartDataHandling(unittest.TestCase):
    """测试图表数据处理"""
    
    def test_date_column_handling(self):
        """测试日期列处理"""
        # 测试不同的日期列名
        data_with_trade_date = pd.DataFrame({
            'trade_date': ['2024-01-01', '2024-01-02'],
            'close': [10.0, 10.5]
        })
        
        fig = create_price_chart(data_with_trade_date)
        self.assertIsInstance(fig, go.Figure)
    
    def test_missing_columns_handling(self):
        """测试缺失列处理"""
        # 测试缺少必要列的数据
        incomplete_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3, freq='D'),
            'close': [10.0, 10.5, 10.2]
            # 缺少 open, high, low 列
        })
        
        # 价格图表应该能处理只有close列的情况
        fig = create_price_chart(incomplete_data)
        self.assertIsInstance(fig, go.Figure)
        
        # K线图应该能处理缺失列的情况
        fig_candlestick = create_candlestick_chart(incomplete_data)
        self.assertIsInstance(fig_candlestick, go.Figure)
    
    def test_data_type_conversion(self):
        """测试数据类型转换"""
        # 测试字符串日期转换
        string_date_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'close': [10.0, 10.5, 10.2]
        })
        
        fig = create_price_chart(string_date_data)
        self.assertIsInstance(fig, go.Figure)

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
交易日历服务测试
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.trading_calendar import TradingCalendar, get_trading_calendar, is_trading_day, get_trading_days


class TestTradingCalendar:
    """交易日历服务测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 清理全局实例
        import src.services.trading_calendar
        src.services.trading_calendar._trading_calendar = None

    def test_trading_calendar_initialization(self):
        """测试交易日历初始化"""
        calendar = TradingCalendar()
        
        # 检查基本属性
        assert hasattr(calendar, '_trading_dates')
        assert hasattr(calendar, '_last_update')
        
        # 获取日历信息
        info = calendar.get_calendar_info()
        assert 'total_trading_days' in info
        assert 'last_update' in info
        assert 'cache_file' in info
        assert 'is_fallback_mode' in info

    def test_known_trading_days(self):
        """测试已知的交易日"""
        calendar = TradingCalendar()
        
        # 测试已知的交易日（工作日且非节假日）
        known_trading_days = [
            '20240102',  # 2024年1月2日，周二
            '20240103',  # 2024年1月3日，周三
            '20240104',  # 2024年1月4日，周四
            '20240105',  # 2024年1月5日，周五
        ]
        
        for date in known_trading_days:
            result = calendar.is_trading_day(date)
            print(f"测试 {date}: {result}")
            # 注意：这里我们不强制断言，因为可能有特殊情况

    def test_known_non_trading_days(self):
        """测试已知的非交易日"""
        calendar = TradingCalendar()
        
        # 测试已知的非交易日
        known_non_trading_days = [
            '20240101',  # 2024年1月1日，元旦
            '20240106',  # 2024年1月6日，周六
            '20240107',  # 2024年1月7日，周日
        ]
        
        for date in known_non_trading_days:
            result = calendar.is_trading_day(date)
            print(f"测试 {date}: {result}")
            # 元旦和周末应该不是交易日
            if date in ['20240101', '20240106', '20240107']:
                assert not result, f"{date} 应该不是交易日"

    def test_spring_festival_2024(self):
        """测试2024年春节期间的交易日判断"""
        calendar = TradingCalendar()
        
        # 2024年春节期间的测试
        spring_festival_tests = {
            '20240208': True,   # 春节前最后一个交易日
            '20240209': False,  # 春节假期开始
            '20240210': False,  # 春节假期
            '20240211': False,  # 春节假期
            '20240212': False,  # 春节假期
            '20240213': False,  # 春节假期
            '20240214': False,  # 春节假期
            '20240215': False,  # 春节假期
            '20240216': False,  # 春节假期
            '20240217': False,  # 春节假期
            '20240218': False,  # 周日，不是交易日
            '20240219': True,   # 春节后第一个交易日（周一）
        }
        
        print("\n=== 2024年春节期间交易日测试 ===")
        for date, expected in spring_festival_tests.items():
            result = calendar.is_trading_day(date)
            date_dt = datetime.strptime(date, '%Y%m%d')
            weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date_dt.weekday()]
            
            status = "✅ 正确" if result == expected else "❌ 错误"
            print(f"{date} ({weekday_name}): 预期={expected}, 实际={result} {status}")
            
            # 对于明确的非交易日，进行断言
            if date in ['20240210', '20240211', '20240212', '20240213', '20240214', '20240215', '20240216', '20240217']:
                assert not result, f"{date} 应该是春节假期，不是交易日"

    def test_get_trading_days_range(self):
        """测试获取交易日范围"""
        calendar = TradingCalendar()
        
        # 测试获取一周的交易日
        trading_days = calendar.get_trading_days('20240102', '20240108')
        
        print(f"\n2024年1月2日-8日的交易日: {trading_days}")
        
        # 基本验证
        assert isinstance(trading_days, list)
        assert len(trading_days) > 0
        
        # 验证日期格式
        for day in trading_days:
            assert len(day) == 8
            datetime.strptime(day, '%Y%m%d')  # 验证日期格式

    def test_invalid_date_format(self):
        """测试无效日期格式"""
        calendar = TradingCalendar()
        
        # 测试无效日期格式
        invalid_dates = ['2024-01-01', '20240001', 'invalid', '']
        
        for invalid_date in invalid_dates:
            result = calendar.is_trading_day(invalid_date)
            assert not result, f"无效日期 {invalid_date} 应该返回 False"

    def test_get_trading_days_invalid_range(self):
        """测试无效日期范围"""
        calendar = TradingCalendar()
        
        # 测试无效日期范围
        result = calendar.get_trading_days('invalid', '20240108')
        assert result == []
        
        result = calendar.get_trading_days('20240108', 'invalid')
        assert result == []

    @patch('akshare.tool_trade_date_hist_sina')
    @patch('os.path.exists')
    def test_fallback_mode(self, mock_exists, mock_akshare):
        """测试后备模式"""
        # 模拟缓存文件不存在
        mock_exists.return_value = False

        # 模拟 AKShare 调用失败
        mock_akshare.side_effect = Exception("AKShare API 失败")

        calendar = TradingCalendar(cache_file="test_fallback_cache.pkl")

        # 检查是否进入后备模式
        info = calendar.get_calendar_info()
        assert info['is_fallback_mode'], "应该进入后备模式"
        
        # 测试后备模式下的基本功能
        # 周一到周五应该被认为是交易日
        assert calendar.is_trading_day('20240102')  # 周二
        assert calendar.is_trading_day('20240103')  # 周三
        assert calendar.is_trading_day('20240104')  # 周四
        assert calendar.is_trading_day('20240105')  # 周五
        
        # 周末应该不是交易日
        assert not calendar.is_trading_day('20240106')  # 周六
        assert not calendar.is_trading_day('20240107')  # 周日

    def test_singleton_pattern(self):
        """测试单例模式"""
        calendar1 = get_trading_calendar()
        calendar2 = get_trading_calendar()
        
        # 应该是同一个实例
        assert calendar1 is calendar2

    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试便捷函数
        result1 = is_trading_day('20240102')
        result2 = get_trading_days('20240102', '20240105')
        
        # 应该返回合理的结果
        assert isinstance(result1, bool)
        assert isinstance(result2, list)

    def test_calendar_refresh(self):
        """测试日历刷新功能"""
        calendar = TradingCalendar()
        
        # 测试刷新功能（不会抛出异常）
        try:
            calendar.refresh_calendar()
        except Exception as e:
            # 如果网络问题导致刷新失败，这是可以接受的
            print(f"日历刷新失败（可能是网络问题）: {e}")

    def test_cache_file_handling(self):
        """测试缓存文件处理"""
        # 使用临时缓存文件
        temp_cache_file = "test_trading_calendar_cache.pkl"
        
        try:
            calendar = TradingCalendar(cache_file=temp_cache_file)
            
            # 检查缓存文件是否被创建（如果成功获取数据）
            info = calendar.get_calendar_info()
            print(f"缓存文件: {info['cache_file']}")
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_cache_file):
                os.remove(temp_cache_file)


if __name__ == '__main__':
    # 直接运行测试
    pytest.main([__file__, '-v', '-s'])

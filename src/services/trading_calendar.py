#!/usr/bin/env python3
"""
交易日历服务 - 提供准确的交易日判断
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Set, List
import logging
from functools import lru_cache
import os
import pickle

logger = logging.getLogger(__name__)


class TradingCalendar:
    """交易日历服务，提供准确的交易日判断"""
    
    def __init__(self, cache_file: str = "data/trading_calendar_cache.pkl"):
        """
        初始化交易日历服务
        
        Args:
            cache_file: 缓存文件路径
        """
        self.cache_file = cache_file
        self._trading_dates: Set[str] = set()
        self._last_update = None
        self._load_or_fetch_calendar()
    
    def _load_or_fetch_calendar(self):
        """加载或获取交易日历"""
        # 尝试从缓存加载
        if self._load_from_cache():
            logger.info("从缓存加载交易日历成功")
            return
        
        # 缓存不存在或过期，从 AKShare 获取
        logger.info("从 AKShare 获取交易日历...")
        self._fetch_from_akshare()
    
    def _load_from_cache(self) -> bool:
        """从缓存文件加载交易日历"""
        try:
            if not os.path.exists(self.cache_file):
                return False
            
            # 检查缓存文件是否过期（超过7天）
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.cache_file))
            if cache_age > timedelta(days=7):
                logger.info("交易日历缓存已过期，需要重新获取")
                return False
            
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                self._trading_dates = cache_data['trading_dates']
                self._last_update = cache_data['last_update']
            
            logger.info(f"从缓存加载了 {len(self._trading_dates)} 个交易日")
            return True
            
        except Exception as e:
            logger.warning(f"加载交易日历缓存失败: {e}")
            return False
    
    def _fetch_from_akshare(self):
        """从 AKShare 获取交易日历"""
        try:
            # 获取交易日历
            trade_cal = ak.tool_trade_date_hist_sina()
            
            # 转换为日期集合
            trade_cal['trade_date'] = pd.to_datetime(trade_cal['trade_date'])
            self._trading_dates = set(trade_cal['trade_date'].dt.strftime('%Y%m%d'))
            self._last_update = datetime.now()
            
            logger.info(f"从 AKShare 获取了 {len(self._trading_dates)} 个交易日")
            
            # 保存到缓存
            self._save_to_cache()
            
        except Exception as e:
            logger.error(f"从 AKShare 获取交易日历失败: {e}")
            # 如果获取失败，使用简化的周末判断作为后备
            logger.warning("使用简化的周末判断作为后备方案")
            self._use_fallback_calendar()
    
    def _save_to_cache(self):
        """保存交易日历到缓存文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            cache_data = {
                'trading_dates': self._trading_dates,
                'last_update': self._last_update
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            logger.info(f"交易日历已保存到缓存: {self.cache_file}")
            
        except Exception as e:
            logger.warning(f"保存交易日历缓存失败: {e}")
    
    def _use_fallback_calendar(self):
        """使用后备的简化交易日历（仅排除周末）"""
        logger.warning("使用后备交易日历：仅排除周末，不考虑节假日")
        # 这里我们不预生成日期，而是在 is_trading_day 中动态判断
        self._trading_dates = set()  # 空集合表示使用后备模式
    
    def is_trading_day(self, date: str) -> bool:
        """
        判断指定日期是否为交易日
        
        Args:
            date: 日期字符串，格式为 YYYYMMDD
            
        Returns:
            True 如果是交易日，False 否则
        """
        # 如果有完整的交易日历，直接查询
        if self._trading_dates:
            return date in self._trading_dates
        
        # 后备方案：仅排除周末
        try:
            date_dt = datetime.strptime(date, '%Y%m%d')
            return date_dt.weekday() < 5  # 周一到周五
        except ValueError:
            logger.error(f"无效的日期格式: {date}")
            return False
    
    def get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """
        获取指定日期范围内的所有交易日
        
        Args:
            start_date: 开始日期，格式为 YYYYMMDD
            end_date: 结束日期，格式为 YYYYMMDD
            
        Returns:
            交易日列表
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
        except ValueError as e:
            logger.error(f"无效的日期格式: {e}")
            return []
        
        trading_days = []
        current_dt = start_dt
        
        while current_dt <= end_dt:
            date_str = current_dt.strftime('%Y%m%d')
            if self.is_trading_day(date_str):
                trading_days.append(date_str)
            current_dt += timedelta(days=1)
        
        return trading_days
    
    def refresh_calendar(self):
        """强制刷新交易日历"""
        logger.info("强制刷新交易日历...")
        self._fetch_from_akshare()
    
    def get_calendar_info(self) -> dict:
        """获取交易日历信息"""
        return {
            'total_trading_days': len(self._trading_dates),
            'last_update': self._last_update,
            'cache_file': self.cache_file,
            'is_fallback_mode': len(self._trading_dates) == 0
        }


# 全局实例
_trading_calendar = None


def get_trading_calendar() -> TradingCalendar:
    """获取交易日历实例（单例模式）"""
    global _trading_calendar
    if _trading_calendar is None:
        _trading_calendar = TradingCalendar()
    return _trading_calendar


# 便捷函数
def is_trading_day(date: str) -> bool:
    """判断是否为交易日的便捷函数"""
    return get_trading_calendar().is_trading_day(date)


def get_trading_days(start_date: str, end_date: str) -> List[str]:
    """获取交易日列表的便捷函数"""
    return get_trading_calendar().get_trading_days(start_date, end_date)


if __name__ == "__main__":
    # 测试代码
    calendar = TradingCalendar()
    
    print("=== 交易日历测试 ===")
    print(f"日历信息: {calendar.get_calendar_info()}")
    
    # 测试2024年春节期间
    test_dates = ['20240208', '20240209', '20240210', '20240218', '20240219']
    print("\n2024年春节期间测试:")
    for date in test_dates:
        result = calendar.is_trading_day(date)
        print(f"{date}: {'✅ 交易日' if result else '❌ 非交易日'}")
    
    # 测试获取交易日列表
    trading_days = calendar.get_trading_days('20240208', '20240220')
    print(f"\n2024-02-08 到 2024-02-20 的交易日: {trading_days}")

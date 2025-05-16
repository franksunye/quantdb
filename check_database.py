"""
查询数据库中的数据，检查测试后的数据状态
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.api.database import get_db, engine
from src.api.models import Asset, DailyStockData
from sqlalchemy.orm import Session

def check_database():
    """查询数据库中的数据"""
    print("正在查询数据库...")

    # 创建数据库会话
    session = next(get_db())

    try:
        # 查询所有资产
        assets = session.query(Asset).all()
        print(f"\n找到 {len(assets)} 个资产:")

        for asset in assets:
            print(f"\n资产ID: {asset.asset_id}, 代码: {asset.symbol}, 名称: {asset.name}")

            # 查询该资产的所有股票数据
            stock_data = session.query(DailyStockData).filter(
                DailyStockData.asset_id == asset.asset_id
            ).order_by(DailyStockData.trade_date).all()

            print(f"  该资产有 {len(stock_data)} 条股票数据:")

            # 打印每条数据的日期和收盘价
            for data in stock_data:
                date_str = data.trade_date.strftime('%Y-%m-%d') if isinstance(data.trade_date, datetime) else data.trade_date
                print(f"  - 日期: {date_str}, 收盘价: {data.close}")

            # 打印日期范围
            if stock_data:
                first_date = stock_data[0].trade_date
                last_date = stock_data[-1].trade_date
                first_date_str = first_date.strftime('%Y-%m-%d') if isinstance(first_date, datetime) else first_date
                last_date_str = last_date.strftime('%Y-%m-%d') if isinstance(last_date, datetime) else last_date
                print(f"  日期范围: {first_date_str} 到 {last_date_str}")

    finally:
        session.close()

if __name__ == "__main__":
    check_database()

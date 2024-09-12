# src\calculate_ma_above_ratio.py
import sqlite3
from datetime import datetime
from src.config import DATABASE_PATH
from src.logger import logger

def calculate_50_ma_above_ratio(start_date, end_date):
    """计算50日均线上的股票占比"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 查询每只股票的收盘价和50日均线
        cursor.execute('''
            SELECT asset_id, trade_date, close,
                   (SELECT AVG(close)
                    FROM daily_stock_data AS ds2
                    WHERE ds2.asset_id = ds1.asset_id
                      AND ds2.trade_date <= ds1.trade_date
                    ORDER BY ds2.trade_date DESC
                    LIMIT 50) AS ma_50
            FROM daily_stock_data AS ds1
            WHERE trade_date BETWEEN ? AND ?
            ORDER BY trade_date, asset_id
        ''', (start_date, end_date))

        stock_data = cursor.fetchall()

        # 准备存放每天的统计数据
        daily_ma_above_ratio = {}
        daily_total_stocks = {}

        for asset_id, trade_date, close_price, ma_50 in stock_data:
            if trade_date not in daily_ma_above_ratio:
                daily_ma_above_ratio[trade_date] = 0
                daily_total_stocks[trade_date] = 0

            # 统计总股票数
            daily_total_stocks[trade_date] += 1

            # 如果收盘价高于50日均线
            if close_price > ma_50:
                daily_ma_above_ratio[trade_date] += 1

        # 计算每日的50日均线上的股票占比
        ma_above_ratios = []
        for trade_date in daily_ma_above_ratio:
            total_stocks = daily_total_stocks[trade_date]
            above_ma_stocks = daily_ma_above_ratio[trade_date]
            ratio = above_ma_stocks / total_stocks if total_stocks > 0 else 0
            ma_above_ratios.append((trade_date, ratio))

        conn.close()

        return ma_above_ratios

    except Exception as e:
        logger.error(f"计算50日均线上的股票占比时发生错误: {e}")
        return None

# 示例用法
if __name__ == "__main__":
    # 设置时间范围
    start_date = "2024-08-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 计算50日均线上的股票占比
    ma_above_ratios = calculate_50_ma_above_ratio(start_date, end_date)

    if ma_above_ratios:
        # 你可以在这里进行绘图或者进一步处理
        for trade_date, ratio in ma_above_ratios:
            print(f"Date: {trade_date}, 50日均线上股票占比: {ratio:.2%}")

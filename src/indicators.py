# src\indicators.py
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from src.config import DATABASE_PATH
from src.logger import logger
import time  # 用于时间记录

def calculate_index_trend(index_id):
    """计算特定指数的每日收盘价"""
    start_time = time.time()  # 记录开始时间
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 获取特定指数的每日收盘价数据
        cursor.execute('''
            SELECT trade_date, close
            FROM daily_stock_data
            WHERE asset_id = ?
            ORDER BY trade_date
        ''', (index_id,))
        index_data = cursor.fetchall()

        conn.close()

        logger.info(f"计算指数趋势耗时: {time.time() - start_time:.2f} 秒")
        return [(trade_date, close_price) for trade_date, close_price in index_data]

    except Exception as e:
        logger.error(f"计算指数趋势时发生错误: {e}")
        return None

def calculate_adl():
    """计算腾落指标（ADL）"""   
    start_time = time.time()  # 记录开始时间
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 获取所有股票的每日收盘价数据
        cursor.execute('''
            SELECT trade_date, asset_id, close
            FROM daily_stock_data
            WHERE close IS NOT NULL
            ORDER BY trade_date, asset_id;
        ''')
        stock_data = cursor.fetchall()

        # 准备存放每天的上涨和下跌股票数量
        daily_changes = {}
        previous_close_prices = {}

        for trade_date, asset_id, close_price in stock_data:
            if trade_date not in daily_changes:
                daily_changes[trade_date] = {'up': 0, 'down': 0}

            if asset_id in previous_close_prices:
                if close_price > previous_close_prices[asset_id]:
                    daily_changes[trade_date]['up'] += 1
                elif close_price < previous_close_prices[asset_id]:
                    daily_changes[trade_date]['down'] += 1

            previous_close_prices[asset_id] = close_price

        # 计算每日的ADL值
        adl = 0
        adl_results = []

        for trade_date in sorted(daily_changes.keys()):
            up_count = daily_changes[trade_date]['up']
            down_count = daily_changes[trade_date]['down']
            net_change = up_count - down_count

            adl += net_change
            adl_results.append((trade_date, adl))

        conn.close()

        logger.info(f"计算ADL耗时: {time.time() - start_time:.2f} 秒")
        return adl_results

    except Exception as e:
        logger.error(f"计算ADL时发生错误: {e}")
        return None

def plot_adl_and_index(adl_results, index_data, start_date_str, end_date_str):
    """绘制ADL和HS300指数图形，并设置时间范围"""
    start_time = time.time()  # 记录开始时间
    try:
        # 转换日期字符串为 datetime 对象
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 筛选在时间范围内的数据
        filtered_adl_results = [(datetime.strptime(date, "%Y-%m-%d"), value) 
                                for date, value in adl_results 
                                if start_date <= datetime.strptime(date, "%Y-%m-%d") <= end_date]
        filtered_index_data = [(datetime.strptime(date, "%Y-%m-%d"), value) 
                               for date, value in index_data 
                               if start_date <= datetime.strptime(date, "%Y-%m-%d") <= end_date]

        if not filtered_adl_results or not filtered_index_data:
            logger.warning("在指定的时间范围内没有数据可绘制")
            return

        # 提取日期和 ADL 值
        adl_dates, adl_values = zip(*filtered_adl_results)
        index_dates, index_values = zip(*filtered_index_data)

        # 创建图形和坐标轴
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 修改颜色
        adl_color = '#ADD8E6'  # 柔和的天蓝色
        hs300_color = '#FFA500'  # 橙色
        
        # 绘制 ADL 曲线
        ax1.plot(adl_dates, adl_values, label='ADL', color=adl_color, linestyle='-', marker='o', markersize=2)
        ax1.set_xlabel('Date')
        ax1.set_ylabel('ADL Value', color='black')
        ax1.tick_params(axis='y', labelcolor='black')

        # 创建第二个坐标轴来绘制指数数据
        ax2 = ax1.twinx()
        ax2.plot(index_dates, index_values, label='HS300 Index', color=hs300_color, linestyle='-', marker='o', markersize=2)
        ax2.set_ylabel('HS300 Index Value', color='black')
        ax2.tick_params(axis='y', labelcolor='black')

        # 设置标题
        fig.suptitle('ADL vs. HS300 Index')

        # 设置日期范围
        ax1.set_xlim(start_date, end_date)

        # 格式化日期显示
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        # 添加网格
        ax1.grid(True)

        # 添加图例
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

        # 自动旋转日期标签
        plt.xticks(rotation=45)

        # 显示图形
        plt.tight_layout()
        plt.show()

        logger.info(f"绘制图形耗时: {time.time() - start_time:.2f} 秒")

    except Exception as e:
        logger.error(f"绘制图形时发生错误: {e}")

if __name__ == "__main__":
    total_start_time = time.time()  # 总执行时间计时开始

    # 计算 ADL 指标
    adl_results = calculate_adl()

    if adl_results:
        # 计算HS300指数数据
        index_data = calculate_index_trend(index_id=10041)

        if index_data:
            # 设置时间范围
            start_date = "2023-03-01"
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # 绘制 ADL 和HS300指数图形
            plot_adl_and_index(adl_results, index_data, start_date, end_date)

    logger.info(f"总执行时间: {time.time() - total_start_time:.2f} 秒")

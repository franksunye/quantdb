# src\calculate_ma_above_ratio.py
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from time import time
from src.config import DATABASE_PATH
from src.logger import logger

# 原始版本的函数
def calculate_50_ma_above_ratio(start_date, end_date):
    """计算50日均线上的股票占比"""
    try:
        start_time = time()  # 开始时间记录
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

        end_time = time()  # 结束时间记录
        logger.info(f"原始函数执行时间: {end_time - start_time:.2f} 秒")

        return ma_above_ratios

    except Exception as e:
        logger.error(f"计算50日均线上的股票占比时发生错误: {e}")
        return None
    
def fetch_data_in_batches(cursor, batch_size):
    """从数据库游标中分批获取数据"""
    while True:
        batch = cursor.fetchmany(batch_size)  # 一次取 batch_size 行数据
        if not batch:
            break  # 如果没有更多数据，退出循环
        yield batch

# 优化版本的函数
def calculate_50_ma_above_ratio_v2(start_date, end_date):
    """使用窗口函数和批量处理优化计算50日均线上的股票占比"""
    try:
        start_time = time()  # 开始时间记录
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 使用窗口函数获取每只股票的50日均线
        cursor.execute('''
            SELECT asset_id, trade_date, close,
                   AVG(close) OVER (PARTITION BY asset_id ORDER BY trade_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50
            FROM daily_stock_data
            WHERE trade_date BETWEEN ? AND ?
            ORDER BY trade_date, asset_id;
        ''', (start_date, end_date))

        # 分批处理数据，避免内存占用过大
        batch_size = 100000
        ma_above_ratios = []
        
        for batch in fetch_data_in_batches(cursor, batch_size):
            df = pd.DataFrame(batch, columns=['asset_id', 'trade_date', 'close', 'ma_50'])
            df['above_ma'] = df['close'] > df['ma_50']
            
            # 修复 DeprecationWarning，使用 `include_groups=False`
            daily_ratios = df.groupby('trade_date', as_index=False, group_keys=False)['above_ma'].mean()
            ma_above_ratios.append(daily_ratios)

        conn.close()

        # 合并所有批次的结果
        final_result = pd.concat(ma_above_ratios)

        end_time = time()  # 结束时间记录
        logger.info(f"优化函数执行时间: {end_time - start_time:.2f} 秒")

        return final_result

    except Exception as e:
        logger.error(f"计算50日均线上的股票占比时发生错误: {e}")
        return None

def plot_ma_above_ratio(ma_above_ratios, start_date_str, end_date_str):
    """绘制50日均线上的股票占比图形，并设置时间范围"""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 筛选在时间范围内的数据
        filtered_data = [(datetime.strptime(date, "%Y-%m-%d"), ratio) 
                         for date, ratio in ma_above_ratios 
                         if start_date <= datetime.strptime(date, "%Y-%m-%d") <= end_date]

        if not filtered_data:
            logger.warning("在指定的时间范围内没有数据可绘制")
            return

        dates, ratios = zip(*filtered_data)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(dates, ratios, label='Above 50-Day MA Ratio', color='#4682B4', linestyle='-', marker='o', markersize=3)
        ax.set_title('Percentage of Stocks Above 50-Day Moving Average')
        ax.set_xlabel('Date')
        ax.set_ylabel('Percentage (%)')

        ax.set_xlim(start_date, end_date)
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}%'))

        ax.grid(True)
        ax.legend(loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        logger.error(f"绘制图形时发生错误: {e}")

def plot_ma_above_ratio_v2(ma_above_ratios, start_date_str, end_date_str):
    """绘制50日均线上的股票占比图形，并设置时间范围，同时增加0%、25%、75%、100%四条参考线"""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 确保数据是 DataFrame 格式，并使用日期作为索引
        if isinstance(ma_above_ratios, pd.DataFrame):
            ma_above_ratios['trade_date'] = pd.to_datetime(ma_above_ratios['trade_date'])
            filtered_data = ma_above_ratios[(ma_above_ratios['trade_date'] >= start_date) & 
                                            (ma_above_ratios['trade_date'] <= end_date)]
        else:
            logger.error("传递的比例数据格式不正确")
            return

        if filtered_data.empty:
            logger.warning("在指定的时间范围内没有数据可绘制")
            return

        # 提取日期和比例
        dates = filtered_data['trade_date']
        ratios = filtered_data['above_ma']

        # 创建图形
        fig, ax = plt.subplots(figsize=(10, 5))

        # 绘制比例曲线
        ax.plot(dates, ratios, label='Above 50-Day MA Ratio', color='orange', linestyle='-', marker='o', markersize=3)

        # 设置标题和标签
        ax.set_title('Percentage of Stocks Above 50-Day Moving Average')
        ax.set_xlabel('Date')
        ax.set_ylabel('Percentage (%)')

        # 设置日期范围
        ax.set_xlim(start_date, end_date)

        # 设置日期格式
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        # 格式化y轴为百分比
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.1f}%'))

        # 添加0%、25%、75%、100%参考线
        ax.axhline(0, color='gray', linestyle='--', linewidth=1, label='0%')  # 0%
        ax.axhline(0.25, color='red', linestyle='--', linewidth=1, label='25%')  # 25%
        ax.axhline(0.75, color='green', linestyle='--', linewidth=1, label='75%')  # 75%
        ax.axhline(1, color='black', linestyle='--', linewidth=1, label='100%')  # 100%

        # 添加网格和图例
        ax.grid(True)
        ax.legend(loc='upper left')

        # 自动旋转日期标签
        plt.xticks(rotation=45)

        # 调整布局，防止标签重叠
        plt.tight_layout()

        # 显示图形
        plt.show()

    except Exception as e:
        logger.error(f"绘制图形时发生错误: {e}")


# 示例用法
if __name__ == "__main__":
    start_date = "2023-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    # # 计算50日均线上的股票占比（原始版本）
    # ma_above_ratios = calculate_50_ma_above_ratio(start_date, end_date)

    # if ma_above_ratios:
    #     for trade_date, ratio in ma_above_ratios:
    #         print(f"Date: {trade_date}, 50日均线上股票占比: {ratio:.2%}")
    #     plot_ma_above_ratio(ma_above_ratios, start_date, end_date)

    # 计算50日均线上的股票占比（优化版本）
    ma_above_ratios_v2 = calculate_50_ma_above_ratio_v2(start_date, end_date)

    if ma_above_ratios_v2 is not None:
        print(ma_above_ratios_v2)
        # 你也可以绘制优化后的结果
        plot_ma_above_ratio_v2(ma_above_ratios_v2, start_date, end_date)

# src/entry_window_performance_analysis.py

import sqlite3
from datetime import datetime, timedelta
from src.logger import logger
from src.config import DATABASE_PATH
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def connect_db(db_path=DATABASE_PATH):
    """连接到SQLite数据库"""
    try:
        conn = sqlite3.connect(db_path)
        logger.info("成功连接到数据库")
        return conn
    except sqlite3.Error as e:
        logger.error(f"连接数据库失败: {e}")
        return None

def calculate_entry_window_performance(conn, window_days):
    """计算指定时间窗口内的交易计划和交易日志的胜率和盈亏比，并绘制图形"""
    cursor = conn.cursor()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=window_days)

    logger.info(f"查询日期范围: {start_date} 到 {end_date}，窗口大小: {window_days}天")

    # 查询在指定时间窗口内的交易计划，基于 entry_date
    cursor.execute(""" 
        SELECT entry_date, status, pnl, entry_price, order_entry 
        FROM trade_plans 
        WHERE entry_date BETWEEN ? AND ? 
    """, (start_date, end_date))

    plans = cursor.fetchall()
    logger.info(f"获取到的交易计划数量: {len(plans)}")

    daily_results_plans = {}

    for entry_date, status, pnl, entry_price, order_entry in plans:
        if entry_date not in daily_results_plans:
            daily_results_plans[entry_date] = {
                'total': 0,
                'wins': 0,
                'total_pnl': 0,
                'total_investment': 0,
                'total_winning_amount': 0,
                'total_losing_amount': 0,
                'net_profit': 0
            }

        # Ensure pnl is not None
        pnl = pnl if pnl is not None else 0.0

        daily_results_plans[entry_date]['total'] += 1
        daily_results_plans[entry_date]['total_investment'] += entry_price * order_entry  # 计算总投入
        daily_results_plans[entry_date]['total_pnl'] += pnl

        if pnl > 0:
            daily_results_plans[entry_date]['wins'] += 1
            daily_results_plans[entry_date]['total_winning_amount'] += pnl
        else:
            daily_results_plans[entry_date]['total_losing_amount'] += abs(pnl)

    # 计算净赚金额并按日期排序
    for date, results in daily_results_plans.items():
        results['net_profit'] = results['total_winning_amount'] - results['total_losing_amount']

    # 准备数据用于绘图
    dates_plans = sorted(daily_results_plans.keys())
    win_rates_plans = [daily_results_plans[date]['wins'] / daily_results_plans[date]['total'] if daily_results_plans[date]['total'] > 0 else 0 for date in dates_plans]
    rois_plans = [daily_results_plans[date]['total_pnl'] / daily_results_plans[date]['total_investment'] if daily_results_plans[date]['total_investment'] > 0 else 0 for date in dates_plans]

    # 将日期字符串转换为datetime对象
    dates_plans = [datetime.strptime(date, '%Y-%m-%d') for date in dates_plans]

    # 计算交易日志的胜率和盈亏比
    cursor.execute(""" 
        SELECT date_entry, status, pnl, entry_price, order_entry 
        FROM trade_logs 
        WHERE date_entry BETWEEN ? AND ? 
    """, (start_date, end_date))

    logs = cursor.fetchall()
    logger.info(f"获取到的交易日志数量: {len(logs)}")

    daily_results_logs = {}

    for date_entry, status, pnl, entry_price, order_entry in logs:
        if date_entry not in daily_results_logs:
            daily_results_logs[date_entry] = {
                'total': 0,
                'wins': 0,
                'total_pnl': 0,
                'total_investment': 0,
                'total_winning_amount': 0,
                'total_losing_amount': 0,
                'net_profit': 0
            }

        # Ensure pnl is not None
        pnl = pnl if pnl is not None else 0.0

        daily_results_logs[date_entry]['total'] += 1
        daily_results_logs[date_entry]['total_investment'] += entry_price * order_entry  # 计算总投入
        daily_results_logs[date_entry]['total_pnl'] += pnl

        if pnl > 0:
            daily_results_logs[date_entry]['wins'] += 1
            daily_results_logs[date_entry]['total_winning_amount'] += pnl
        else:
            daily_results_logs[date_entry]['total_losing_amount'] += abs(pnl)

    # 计算净赚金额并按日期排序
    for date, results in daily_results_logs.items():
        results['net_profit'] = results['total_winning_amount'] - results['total_losing_amount']

    # 准备数据用于绘图
    dates_logs = sorted(daily_results_logs.keys())
    win_rates_logs = [daily_results_logs[date]['wins'] / daily_results_logs[date]['total'] if daily_results_logs[date]['total'] > 0 else 0 for date in dates_logs]
    rois_logs = [daily_results_logs[date]['total_pnl'] / daily_results_logs[date]['total_investment'] if daily_results_logs[date]['total_investment'] > 0 else 0 for date in dates_logs]

    # 将日期字符串转换为datetime对象
    dates_logs = [datetime.strptime(date, '%Y-%m-%d') for date in dates_logs]

    # 创建图形和子图，设置共享X轴
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), sharex=True)

    # 绘制交易计划的胜率
    ax1.set_ylabel('胜率', color='blue', fontproperties='SimHei')
    ax1.plot(dates_plans, win_rates_plans, marker='o', label='交易计划胜率', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 在胜率数据点上标出数值
    for i, win_rate in enumerate(win_rates_plans):
        ax1.text(dates_plans[i], win_rate, f'{win_rate:.2%}', color='blue', fontsize=9, ha='center', va='bottom')

    # 创建第二个Y轴
    ax1_twin = ax1.twinx()
    ax1_twin.set_ylabel('盈亏比', color='orange', fontproperties='SimHei')
    ax1_twin.plot(dates_plans, rois_plans, marker='x', label='交易计划盈亏比', color='orange')
    ax1_twin.tick_params(axis='y', labelcolor='orange')

    # 在盈亏比数据点上标出数值
    for i, roi in enumerate(rois_plans):
        ax1_twin.text(dates_plans[i], roi, f'{roi:.2f}', color='orange', fontsize=9, ha='center', va='bottom')

        # 如果盈亏比为负，圈出并标注日期和盈亏值
        if roi < 0:
            ax1_twin.scatter(dates_plans[i], roi, color='red', s=100, edgecolor='black')  # 圈出负盈亏比的点
            ax1_twin.text(dates_plans[i] + timedelta(days=0.2), roi, f'{roi:.2f} ({dates_plans[i].strftime("%m-%d")})', color='red', fontsize=9, ha='left', va='center')

    # 添加零线
    ax1_twin.axhline(0, color='orange', linewidth=2.0, linestyle='--')

    # 设置标题
    ax1.set_title(f'交易计划在过去{window_days}天内的胜率和盈亏比变化', fontproperties='SimHei')

    # 绘制交易日志的胜率
    ax2.set_ylabel('胜率', color='green', fontproperties='SimHei')
    ax2.plot(dates_logs, win_rates_logs, marker='o', label='交易日志胜率', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    # 在胜率数据点上标出数值
    for i, win_rate in enumerate(win_rates_logs):
        ax2.text(dates_logs[i], win_rate, f'{win_rate:.2%}', color='green', fontsize=9, ha='center', va='bottom')

    # 创建第二个Y轴
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('盈亏比', color='purple', fontproperties='SimHei')
    ax2_twin.plot(dates_logs, rois_logs, marker='x', label='交易日志盈亏比', color='purple')
    ax2_twin.tick_params(axis='y', labelcolor='purple')

    # 在盈亏比数据点上标出数值
    for i, roi in enumerate(rois_logs):
        ax2_twin.text(dates_logs[i], roi, f'{roi:.2f}', color='purple', fontsize=9, ha='center', va='bottom')

        # 如果盈亏比为负，圈出并标注日期和盈亏值
        if roi < 0:
            ax2_twin.scatter(dates_logs[i], roi, color='red', s=100, edgecolor='black')  # 圈出负盈亏比的点
            ax2_twin.text(dates_logs[i] + timedelta(days=0.2), roi, f'{roi:.2f} ({dates_logs[i].strftime("%m-%d")})', color='red', fontsize=9, ha='left', va='center')

    # 添加零线
    ax2_twin.axhline(0, color='purple', linewidth=2.0, linestyle='--')

    # 设置标题
    ax2.set_title(f'交易日志在过去{window_days}天内的胜率和盈亏比变化', fontproperties='SimHei')

    # 自动调整布局
    fig.tight_layout()
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()

    # 输出结果
    for date in sorted(daily_results_plans.keys()):
        results = daily_results_plans[date]
        win_rate = results['wins'] / results['total'] if results['total'] > 0 else 0
        roi = results['total_pnl'] / results['total_investment'] if results['total_investment'] > 0 else 0
        logger.info(f"{date} - 交易计划总交易数: {results['total']}, 胜率: {win_rate:.2%}, 盈亏比: {roi:.2f}")
        logger.info(f"总投入: {results['total_investment']:.2f}, 赢的金额: {results['total_winning_amount']:.2f}, 亏的金额: {results['total_losing_amount']:.2f}, 净赚金额: {results['net_profit']:.2f}")

    for date in sorted(daily_results_logs.keys()):
        results = daily_results_logs[date]
        win_rate = results['wins'] / results['total'] if results['total'] > 0 else 0
        roi = results['total_pnl'] / results['total_investment'] if results['total_investment'] > 0 else 0
        logger.info(f"{date} - 交易日志总交易数: {results['total']}, 胜率: {win_rate:.2%}, 盈亏比: {roi:.2f}")
        logger.info(f"总投入: {results['total_investment']:.2f}, 赢的金额: {results['total_winning_amount']:.2f}, 亏的金额: {results['total_losing_amount']:.2f}, 净赚金额: {results['net_profit']:.2f}")

def main():
    conn = connect_db()
    if conn is None:
        return

    try:
        # 这里可以添加用户输入的时间窗口
        window_days = int(input("请输入时间窗口（天数）: "))
        calculate_entry_window_performance(conn, window_days)
    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()

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

def calculate_daily_win_rate_and_roi(conn):
    """计算最近20天内每天的胜率和盈亏比"""
    cursor = conn.cursor()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=20)

    logger.info(f"查询日期范围: {start_date} 到 {end_date}")

    # 查询最近20天内的交易计划，基于 exit_date
    cursor.execute("""
        SELECT exit_date, status, pnl, entry_price, order_entry
        FROM trade_plans
        WHERE exit_date BETWEEN ? AND ?
    """, (start_date, end_date))

    plans = cursor.fetchall()
    logger.info(f"获取到的交易计划数量: {len(plans)}")

    if not plans:
        logger.info("在最近20天内没有交易计划")
        return [], []  # 返回空列表以便后续处理

    daily_results = {}

    for exit_date, status, pnl, entry_price, order_entry in plans:
        if exit_date not in daily_results:
            daily_results[exit_date] = {
                'total': 0,
                'wins': 0,
                'total_pnl': 0,
                'total_investment': 0,
                'total_winning_amount': 0,
                'total_losing_amount': 0,
                'net_profit': 0  # 新增净赚金额字段
            }

        daily_results[exit_date]['total'] += 1
        daily_results[exit_date]['total_investment'] += entry_price * order_entry  # 计算总投入

        if status == 'COMPLETED':
            daily_results[exit_date]['total_pnl'] += pnl
            if pnl > 0:
                daily_results[exit_date]['wins'] += 1
                daily_results[exit_date]['total_winning_amount'] += pnl  # 计算赢得的金额
            else:
                daily_results[exit_date]['total_losing_amount'] += abs(pnl)  # 计算亏损的金额

    # 计算净赚金额并按日期排序
    for date, results in daily_results.items():
        results['net_profit'] = results['total_winning_amount'] - results['total_losing_amount']

    # 准备数据用于绘图
    dates = sorted(daily_results.keys())
    win_rates = [daily_results[date]['wins'] / daily_results[date]['total'] if daily_results[date]['total'] > 0 else 0 for date in dates]
    rois = [daily_results[date]['total_pnl'] / daily_results[date]['total_investment'] if daily_results[date]['total_investment'] > 0 else 0 for date in dates]

    # 将日期字符串转换为datetime对象
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]

    # 绘制胜率和盈亏比的变化图
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 绘制胜率
    ax1.set_xlabel('日期', fontproperties='SimHei')
    ax1.set_ylabel('胜率', color='blue', fontproperties='SimHei')
    ax1.plot(dates, win_rates, marker='o', label='胜率', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 在胜率数据点上标出数值
    for i, win_rate in enumerate(win_rates):
        ax1.text(dates[i], win_rate, f'{win_rate:.2%}', color='blue', fontsize=9, ha='center', va='bottom')

    # 创建第二个Y轴
    ax2 = ax1.twinx()
    ax2.set_ylabel('盈亏比', color='orange', fontproperties='SimHei')
    ax2.plot(dates, rois, marker='x', label='盈亏比', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    # 在盈亏比数据点上标出数值
    for i, roi in enumerate(rois):
        ax2.text(dates[i], roi, f'{roi:.2f}', color='orange', fontsize=9, ha='center', va='bottom')

    # 添加零线
    ax2.axhline(0, color='orange', linewidth=2.0, linestyle='--')

    # 设置X轴的日期格式
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

    # 设置标题和图例
    plt.title('交易计划100%执行，胜率和盈亏比随时间的变化', fontproperties='SimHei')
    fig.tight_layout()  # 自动调整布局
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()

    # 输出结果
    for date in sorted(daily_results.keys()):
        results = daily_results[date]
        win_rate = results['wins'] / results['total'] if results['total'] > 0 else 0
        roi = results['total_pnl'] / results['total_investment'] if results['total_investment'] > 0 else 0
        logger.info(f"{date} - 总交易数: {results['total']}, 胜率: {win_rate:.2%}, 盈亏比: {roi:.2f}")
        logger.info(f"总投入: {results['total_investment']:.2f}, 赢的金额: {results['total_winning_amount']:.2f}, 亏的金额: {results['total_losing_amount']:.2f}, 净赚金额: {results['net_profit']:.2f}")

def main():
    conn = connect_db()
    if conn is None:
        return

    try:
        calculate_daily_win_rate_and_roi(conn)
    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()
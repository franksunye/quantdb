# src\update_trade_plan_metrics.py
import sqlite3
from datetime import datetime
from src.logger import logger

def connect_db(db_path='database/stock_data.db'):
    """连接到SQLite数据库"""
    try:
        conn = sqlite3.connect(db_path)
        logger.info("成功连接到数据库")
        return conn
    except sqlite3.Error as e:
        logger.error(f"连接数据库失败: {e}")
        return None

def fetch_completed_trade_plans(conn):
    """获取所有状态为 COMPLETED 的交易计划"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT plan_id, entry_price, exit_price, entry_date, exit_date, asset_id, order_entry 
            FROM trade_plans 
            WHERE status = 'COMPLETED'
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"获取已完成交易计划失败: {e}")
        return []

def calculate_pnl(entry_price, exit_price, order_entry):
    """计算盈亏"""
    return round((exit_price * order_entry) - (entry_price * order_entry), 2)

def fetch_high_low_prices(conn, asset_id, start_date, end_date):
    """获取指定日期范围内的最高价和最低价"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT MAX(high), MIN(low)
            FROM daily_stock_data
            WHERE asset_id = ? AND trade_date BETWEEN ? AND ?
        """, (asset_id, start_date, end_date))
        return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"获取最高价和最低价失败: {e}")
        return None, None

def update_trade_plan(conn, plan_id, pnl, high, low):
    """更新交易计划的 PNL、最高价和最低价"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE trade_plans
            SET pnl = ?, high = ?, low = ?
            WHERE plan_id = ?
        """, (pnl, high, low, plan_id))
        conn.commit()
        logger.info(f"成功更新交易计划 ID {plan_id} 的 PNL、最高价和最低价")
    except sqlite3.Error as e:
        logger.error(f"更新交易计划 ID {plan_id} 时发生错误: {e}")
        conn.rollback()

def fetch_pending_and_active_trade_plans(conn):
    """获取所有状态为 PENDING 和 ACTIVE 的交易计划"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT plan_id, entry_price, asset_id, order_entry 
            FROM trade_plans 
            WHERE status IN ('PENDING', 'ACTIVE')
        """)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"获取待处理和活动交易计划失败: {e}")
        return []

def fetch_current_high_low_close_prices(conn, asset_id):
    """获取当前日期的最高价、最低价和收盘价"""
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        cursor.execute("""
            SELECT MAX(high), MIN(low), close
            FROM daily_stock_data
            WHERE asset_id = ? AND trade_date = ?
        """, (asset_id, today))
        return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"获取当前最高价、最低价和收盘价失败: {e}")
        return None, None, None

def calculate_potential_pnl(entry_price, current_close, order_entry):
    """计算潜在盈亏"""
    return round((current_close * order_entry) - (entry_price * order_entry), 2)

def update_active_and_pending_trade_plan_metrics():
    """更新待处理和活动交易计划的指标"""
    conn = connect_db()
    if conn is None:
        return

    try:
        # Fetch both PENDING and ACTIVE trade plans
        pending_and_active_plans = fetch_pending_and_active_trade_plans(conn)
        for plan in pending_and_active_plans:
            plan_id, entry_price, asset_id, order_entry = plan
            
            # 获取当前最高价、最低价和收盘价
            current_high, current_low, current_close = fetch_current_high_low_close_prices(conn, asset_id)
            
            if current_high is not None:
                # 计算潜在 PNL
                potential_pnl = calculate_potential_pnl(entry_price, current_close, order_entry)
                
                # 更新交易计划
                update_trade_plan(conn, plan_id, potential_pnl, current_high, current_low)

    finally:
        conn.close()
        logger.info("数据库连接已关闭")

def update_trade_plan_metrics():
    """更新交易计划的指标"""
    conn = connect_db()
    if conn is None:
        return

    try:
        completed_plans = fetch_completed_trade_plans(conn)
        for plan in completed_plans:
            plan_id, entry_price, exit_price, entry_date, exit_date, asset_id, order_entry = plan
            
            # 计算 PNL
            pnl = calculate_pnl(entry_price, exit_price, order_entry)
            
            # 获取交易区间的最高价和最低价
            high, low = fetch_high_low_prices(conn, asset_id, entry_date, exit_date)
            
            # 更新交易计划
            update_trade_plan(conn, plan_id, pnl, high, low)

    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    update_trade_plan_metrics()
    update_active_and_pending_trade_plan_metrics()

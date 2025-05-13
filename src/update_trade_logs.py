import sqlite3
from datetime import datetime
from src.logger import logger
from src.database import get_asset_id

def connect_db(db_path='database/stock_data.db'):
    """连接到SQLite数据库"""
    try:
        conn = sqlite3.connect(db_path)
        logger.info("成功连接到数据库")
        return conn
    except sqlite3.Error as e:
        logger.error(f"连接数据库失败: {e}")
        return None

def fetch_hold_and_live_trade_logs(conn):
    """获取所有状态为 HOLD 和 LIVE 的交易日志"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT log_id, plan_id, stock_code, stock_name, entry_price, date_entry, order_entry 
            FROM trade_logs 
            WHERE status IN ('HOLD', 'LIVE')
        """)
        logs = cursor.fetchall()
        logger.info(f"成功获取到 {len(logs)} 个 HOLD 和 LIVE 状态的交易日志")
        return logs
    except sqlite3.Error as e:
        logger.error(f"获取 HOLD 和 LIVE 交易日志失败: {e}")
        return []

def fetch_current_close_price(conn, stock_code):
    """获取当前日期的收盘价"""
    asset_id = get_asset_id(conn, stock_code)
    if asset_id is None:
        logger.warning(f"未找到资产 ID 对应的股票代码: {stock_code}")
        return None

    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        cursor.execute("""
            SELECT close
            FROM daily_stock_data
            WHERE asset_id = ? AND trade_date = ?
        """, (asset_id, today))
        result = cursor.fetchone()
        if result:
            logger.info(f"成功获取 {stock_code} 的当前收盘价: {result[0]}")
            return result[0]
        else:
            logger.warning(f"未找到 {stock_code} 的当前收盘价")
            return None
    except sqlite3.Error as e:
        logger.error(f"获取当前收盘价失败: {e}")
        return None

def calculate_pnl(entry_price, current_price, order_entry):
    """计算盈亏"""
    pnl = round((current_price * order_entry) - (entry_price * order_entry), 2)
    logger.debug(f"计算盈亏: entry_price={entry_price}, current_price={current_price}, order_entry={order_entry}, pnl={pnl}")
    return pnl

def update_trade_log(conn, log_id, pnl, current_price):
    """更新交易日志的 PNL 和当前价格"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE trade_logs
            SET pnl = ?, current_price = ?
            WHERE log_id = ?
        """, (pnl, current_price, log_id))
        conn.commit()
        logger.info(f"成功更新交易日志 ID {log_id} 的 PNL 和当前价格")
    except sqlite3.Error as e:
        logger.error(f"更新交易日志 ID {log_id} 时发生错误: {e}")
        conn.rollback()

def update_trade_logs_metrics():
    """更新交易日志的指标"""
    conn = connect_db()
    if conn is None:
        logger.error("数据库连接失败，无法更新交易日志")
        return

    try:
        # Fetch both HOLD and LIVE trade logs
        hold_and_live_logs = fetch_hold_and_live_trade_logs(conn)
        for log in hold_and_live_logs:
            log_id, plan_id, stock_code, stock_name, entry_price, date_entry, order_entry = log
            
            logger.info(f"处理交易日志 ID {log_id}: stock_code={stock_code}, entry_price={entry_price}, order_entry={order_entry}")
            
            # 获取当前收盘价
            current_price = fetch_current_close_price(conn, stock_code)
            
            if current_price is not None:
                # 计算 PNL
                pnl = calculate_pnl(entry_price, current_price, order_entry)
                
                # 更新交易日志
                update_trade_log(conn, log_id, pnl, current_price)
            else:
                logger.warning(f"无法计算 PNL，因为未获取到当前价格 for log_id={log_id}")

    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    update_trade_logs_metrics()

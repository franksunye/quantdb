# src\generate_trade_logs.py
import sqlite3
from src.logger import logger  # 引入项目的日志模块

def connect_db(db_path='database/stock_data.db'):
    """连接到SQLite数据库"""
    try:
        conn = sqlite3.connect(db_path)
        logger.info("成功连接到数据库")
        return conn
    except sqlite3.Error as e:
        logger.error(f"连接数据库失败: {e}")
        return None

def fetch_active_trade_plans(conn):
    """获取所有状态为 ACTIVE 且未转为日志的交易计划"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM trade_plans WHERE status = 'ACTIVE' AND logged = 0")
        active_plans = cursor.fetchall()
        logger.info(f"成功获取到 {len(active_plans)} 个ACTIVE状态且未转为日志的交易计划")
        return active_plans
    except sqlite3.Error as e:
        logger.error(f"获取ACTIVE状态的交易计划失败: {e}")
        return []

def insert_trade_log(conn, trade_plan):
    """将交易计划插入到交易日志中"""
    cursor = conn.cursor()
    
    log_data = (
        trade_plan[0],         # plan_id
        trade_plan[5],         # stock_code
        trade_plan[4],         # stock_name
        'LIVE',                # status (初始状态设为 'live')
        trade_plan[7],         # entry_price
        trade_plan[8],         # date_entry
        trade_plan[9],         # order_entry
        trade_plan[10],         # slip_entry
        trade_plan[11],        # comm_entry
        trade_plan[12],        # exit_price
        trade_plan[13],        # date_exit
        trade_plan[14]         # order_exit
    )

    try:
        cursor.execute("""
            INSERT INTO trade_logs (
                plan_id, stock_code, stock_name, status, entry_price, date_entry, order_entry, slip_entry, 
                comm_entry, exit_price, date_exit, order_exit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, log_data)
        
        # 更新 trade_plans 表中的 logged 字段
        cursor.execute("UPDATE trade_plans SET logged = 1 WHERE plan_id = ?", (trade_plan[0],))
        conn.commit()
        logger.info(f"成功将交易计划 ID {trade_plan[0]} 插入到交易日志，并更新 logged 状态")
    except sqlite3.Error as e:
        logger.error(f"插入交易日志或更新交易计划时发生错误: {e}")
        conn.rollback()  # 回滚事务，确保数据库一致性

def generate_trade_logs():
    logger.info("交易日志生成程序开始执行")
    conn = connect_db()
    if conn is not None:
        active_plans = fetch_active_trade_plans(conn)
        for plan in active_plans:
            insert_trade_log(conn, plan)
        conn.close()
        logger.info("交易日志已生成，并更新了相关交易计划的状态。")
    else:
        logger.error("由于数据库连接失败，交易日志生成程序未能成功执行")

if __name__ == "__main__":
    generate_trade_logs()

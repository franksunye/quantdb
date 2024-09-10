# src\signal_to_plan.py
import sqlite3
from src.logger import logger
from datetime import datetime

def get_signal_data(conn):
    """
    从 trade_signals 表中获取未生成计划的信号
    """
    query = '''
    SELECT signal_id, strategy_id, asset_id, signal_date, signal_type, signal_strength, price_at_signal, suggested_quantity, optimal_result
    FROM trade_signals
    WHERE plan_generated = 0
    '''
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        signals = cursor.fetchall()
        logger.info("成功从 trade_signals 表中读取未生成计划的信号")
        return signals
    except sqlite3.Error as e:
        logger.error(f"从 trade_signals 表中读取数据时发生错误: {e}")
        raise

def get_asset_data(conn, asset_id):
    """
    从 assets 表中获取资产的名称和代码
    """
    query = 'SELECT name, symbol FROM assets WHERE asset_id = ?'
    cursor = conn.cursor()
    try:
        cursor.execute(query, (asset_id,))
        asset = cursor.fetchone()
        if asset:
            logger.info(f"成功获取资产数据: asset_id={asset_id}")
        else:
            logger.warning(f"资产 ID {asset_id} 不存在于 assets 表中")
        return asset
    except sqlite3.Error as e:
        logger.error(f"从 assets 表中获取资产数据时发生错误: {e}")
        raise

def insert_trade_plan(conn, signal, asset_data):
    """
    将信号数据插入到 trade_plans 表中
    """
    signal_id, strategy_id, asset_id, signal_date, signal_type, signal_strength, price_at_signal, suggested_quantity, optimal_result = signal
    asset_name, symbol = asset_data
    
    # 示例数据填充
    plan_date = datetime.now().date()
    status = 'PENDING'  # 假设初始状态为 PENDING
    entry_price = price_at_signal
    entry_date = signal_date
    order_entry = suggested_quantity
    slip_entry = 0.01  # 示例滑点
    comm_entry = 0.01  # 示例佣金
    
    query = '''
    INSERT INTO trade_plans (
        plan_date, signal_id, asset_id, asset_name, symbol, status, entry_price, entry_date,
        order_entry, slip_entry, comm_entry
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    params = (
        plan_date, signal_id, asset_id, asset_name, symbol, status, entry_price, entry_date,
        order_entry, slip_entry, comm_entry
    )
    
    logger.debug(f"执行 SQL: {query}")
    logger.debug(f"参数: {params}")
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        logger.info(f"成功将信号 {signal_id} 插入到 trade_plans 表中")
    except sqlite3.Error as e:
        logger.error(f"将信号 {signal_id} 插入到 trade_plans 表时发生错误: {e}")
        conn.rollback()
        raise
        
def update_signal_plan_generated(conn, signal_id):
    """
    更新信号记录，标记为已生成计划
    """
    query = 'UPDATE trade_signals SET plan_generated = 1 WHERE signal_id = ?'
    cursor = conn.cursor()
    try:
        cursor.execute(query, (signal_id,))
        conn.commit()
        logger.info(f"成功更新信号 {signal_id} 为已生成计划")
    except sqlite3.Error as e:
        logger.error(f"更新信号 {signal_id} 为已生成计划时发生错误: {e}")
        conn.rollback()
        raise

def main():
    db_file_path = 'database/stock_data.db'
    logger.info(f"连接到数据库: {db_file_path}")
    conn = sqlite3.connect(db_file_path)
    
    try:
        signals = get_signal_data(conn)
        for signal in signals:
            asset_id = signal[2]
            asset_data = get_asset_data(conn, asset_id)
            if asset_data:
                insert_trade_plan(conn, signal, asset_data)
                update_signal_plan_generated(conn, signal[0])
                logger.info(f"成功生成交易计划并更新信号: {signal[0]}")
            else:
                logger.warning(f"无法生成交易计划，资产 ID {asset_id} 不存在")
    
    except sqlite3.Error as e:
        logger.error(f"数据库操作过程中发生错误: {e}")
    
    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == '__main__':
    main()

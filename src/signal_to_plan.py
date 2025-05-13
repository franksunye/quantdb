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
    
    # logger.debug(f"执行 SQL: {query}")
    # logger.debug(f"参数: {params}")
    
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

def process_sell_signals(conn, sell_signal):
    """
    处理 SELL 信号，查找对应的 BUY 信号，并更新 trade_plans 表中的记录
    """
    signal_id, strategy_id, asset_id, signal_date, signal_type, signal_strength, price_at_signal, suggested_quantity, optimal_result = sell_signal

    # 查找未匹配 exit 的 BUY 信号的交易计划
    query = '''
    SELECT plan_id, entry_date, entry_price, order_entry
    FROM trade_plans
    WHERE asset_id = ? AND exit_date IS NULL
    ORDER BY entry_date DESC
    LIMIT 1
    '''
    cursor = conn.cursor()
    try:
        cursor.execute(query, (asset_id,))
        buy_plan = cursor.fetchone()
        if buy_plan:
            plan_id, entry_date, entry_price, order_entry = buy_plan

            # 更新交易计划中的 exit 信息
            update_query = '''
            UPDATE trade_plans
            SET exit_price = ?, exit_date = ?, order_exit = ?, status = 'COMPLETED'
            WHERE plan_id = ?
            '''
            update_params = (price_at_signal, signal_date, suggested_quantity, plan_id)
            
            # logger.debug(f"执行 SQL: {update_query}")
            # logger.debug(f"参数: {update_params}")

            cursor.execute(update_query, update_params)
            conn.commit()
            logger.info(f"成功更新交易计划 ID {plan_id}，匹配 SELL 信号 {signal_id}")
        else:
            logger.warning(f"未找到匹配的 BUY 信号来处理 SELL 信号 {signal_id}")

    except sqlite3.Error as e:
        logger.error(f"处理 SELL 信号时发生错误: {e}")
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
            signal_type = signal[4]
            asset_data = get_asset_data(conn, asset_id)
            if asset_data:
                if signal_type == 'BUY':
                    insert_trade_plan(conn, signal, asset_data)
                    update_signal_plan_generated(conn, signal[0])
                    logger.info(f"成功生成交易计划并更新信号: {signal[0]}")
                elif signal_type.startswith('SELL'):
                    process_sell_signals(conn, signal)
                    update_signal_plan_generated(conn, signal[0])
                    logger.info(f"成功处理 SELL 信号并更新信号: {signal[0]}")
            else:
                logger.warning(f"无法生成交易计划，资产 ID {asset_id} 不存在")
    
    except sqlite3.Error as e:
        logger.error(f"数据库操作过程中发生错误: {e}")
    
    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == '__main__':
    main()

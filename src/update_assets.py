import akshare as ak
import sqlite3
from src.config import DATABASE_PATH
from src.database import get_asset_id, insert_asset, update_asset
from src.logger import logger

def update_assets_with_realtime_data():
    """
    使用股票实时数据更新 assets 表
    """
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # 下载所有股票的实时数据
        realtime_data = ak.stock_zh_a_spot_em()
        logger.debug(f"Downloaded {len(realtime_data)} stocks' real-time data.")
        
        for _, row in realtime_data.iterrows():
            symbol = row['代码']
            name = row['名称']
            
            # 查询是否已存在该股票
            asset_id = get_asset_id(conn, symbol)
            
            if asset_id is None:
                # 如果不存在，则插入新记录
                insert_asset(
                    conn = conn,
                    symbol=symbol,
                    name=name,
                    isin=symbol,
                    asset_type='stock',
                    exchange='沪深',
                    currency='CNY'
                )
                logger.info(f"Added new stock: {symbol} - {name}")
            else:
                # 如果存在，检查名称是否一致
                existing_name = get_asset_name_by_symbol(conn, symbol)
                
                if existing_name != name:
                    update_asset(conn, asset_id, name=name)
                    logger.info(f"Updated name for {symbol}: {existing_name} -> {name}")
                else:
                    logger.info(f"No change needed for {symbol}: {name}")
        
        conn.commit()
        logger.info("Assets table updated successfully")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error occurred during update: {str(e)}")
    
    finally:
        conn.close()

def get_asset_name_by_symbol(conn, symbol):
    """
    根据股票代码查询资产名称
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM assets WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    return result[0] if result else None

if __name__ == "__main__":
    update_assets_with_realtime_data()
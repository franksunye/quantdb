# src/updater.py

from src.downloader import download_index_data
from src.database import insert_asset

def update_index_data(index_name, index_symbol):
    """更新指数成分股数据"""
    data = download_index_data(index_symbol)
    for _, row in data.iterrows():
        # 假设从akshare下载的数据包含'stock_code', 'stock_name'
        insert_asset(row['stock_code'], row['stock_name'], row['stock_code'], 'stock', 'SHSE' if row['stock_code'].startswith('6') else 'SZSE', 'CNY')

    print(f"{index_name} data updated.")

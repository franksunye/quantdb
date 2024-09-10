# src/downloader.py

import akshare as ak
import pandas as pd

def download_index_data(index_symbol: str) -> pd.DataFrame:
    """下载指数成分股数据"""
    return ak.index_stock_cons(symbol=index_symbol)

def save_raw_data(data: pd.DataFrame, filename: str):
    """保存原始数据到文件"""
    file_path = f"{filename}.csv"
    data.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")

def format_data_for_db(data: pd.DataFrame) -> pd.DataFrame:
    """格式化数据以适应数据库的结构"""
    return data[['品种代码', '品种名称', '纳入日期']].rename(
        columns={'品种代码': 'symbol', '品种名称': 'name', '纳入日期': 'inclusion_date'})


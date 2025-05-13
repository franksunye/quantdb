# src/processor.py

import pandas as pd

def format_data(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """根据数据类型（股票/指数）格式化数据"""
    if data_type == "stock":
        required_columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
    elif data_type == "index":
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    else:
        raise ValueError("Unsupported data type")

    for col in required_columns:
        if col not in df.columns:
            df[col] = pd.NA

    return df

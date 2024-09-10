# src/config.py

import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../database/stock_data.db')
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), '../data/raw/')
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../data/processed/')

# Indices configuration
INDEX_CONFIG = {
    "000300": "沪深300",
    "000905": "中证500", # 中证小盘500指数
    "000904": "中证200", # 中证中盘200指数
    "000903": "中证100", 
    "000852": "中证1000",
    "932000": "中证2000",  
    "000699": "科创200",
    "000698": "科创100",
    "000688": "科创50",
    "399006": "创业板指",
    "000001": "上证指数",
    "399001": "深证成指",
}

# Function to convert index config to list of dictionaries
def indices_to_list(config):
    return [
        {
            "code": code,
            "name": name,
            "csv": f"{code}_{name.replace(' ', '_').lower()}.csv"
        }
        for code, name in config.items()
    ]

# Get the list of indices
INDICES = indices_to_list(INDEX_CONFIG)
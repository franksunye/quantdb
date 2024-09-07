# src/config.py

import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../database/stock_data.db')
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), '../data/raw/')
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../data/processed/')

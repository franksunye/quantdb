# src/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from src.signal_sender import process_signals
import sqlite3

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: process_signals(sqlite3.connect('database/stock_data.db')),
        'interval',
        minutes=5  # 每5分钟检查一次
    )
    scheduler.start()

if __name__ == '__main__':
    start_scheduler()


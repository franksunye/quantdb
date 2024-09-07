# src/scheduler.py

import schedule
import time
from src.updater import update_index_data

def job():
    """定义定时任务"""
    update_index_data("科创50", "000688")
    update_index_data("沪深300", "000300")

def start_scheduler():
    """启动定时任务调度"""
    schedule.every().day.at("09:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

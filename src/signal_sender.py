# src/signal_sender.py
import sqlite3
import requests
from src.database import get_pending_signals, mark_signal_as_sent, fetch_signal_target
from src.logger import logger

def post_text_to_webhook(message, webhook_url):
    """发送信号到Webhook"""
    post_data = {
        'msgtype': "text",
        'text': {
            'content': message,
            'mentioned_mobile_list': [18600372156],
        },
    }
    
    try:
        response = requests.post(webhook_url, json=post_data)
        response.raise_for_status()
        logger.info(f"sendToWebhook: Response status: {response.status_code}")
        logger.info(f"sendToWebhook: Webhook URL: {webhook_url}")
        logger.info(f"sendToWebhook: Message content: {message[:100]}...")  # 只显示前100个字符
    except requests.exceptions.RequestException as e:
        logger.error(f"sendToWebhook: 发送到Webhook时发生错误: {e}")

def process_signals(conn):
    """处理待发送的信号"""
    webhook_url = fetch_signal_target()
    logger.info(f"process_signals: Fetching webhook URL: {webhook_url}")
    pending_signals = get_pending_signals(conn)
    logger.info(f"process_signals: Found {len(pending_signals)} pending signals")
    
    for signal in pending_signals:
        signal_id, strategy_id, asset_id, signal_date, signal_type, signal_strength, price_at_signal, suggested_quantity, optimal_result, notes = signal
        message = f'''
        策略ID: {strategy_id}, 股票ID: {asset_id}, 信号日期: {signal_date}, 
        信号类型: {signal_type}, 信号强度: {signal_strength}, 
        信号价格: {price_at_signal}, 建议数量: {suggested_quantity}, 
        最佳结果: {optimal_result}, 备注: {notes}
        '''
        logger.info(f"process_signals: Sending signal: {message}...")
        # logger.info(f"process_signals: Sending signal: {message[:50]}...")
        # post_text_to_webhook(message, webhook_url)
        logger.info(f"process_signals: Marked signal {signal_id} as sent")
        mark_signal_as_sent(conn, signal_id)  # 更新信号状态为已发送
        logger.info(f"mark_signal_as_sent: Successfully marked signal {signal_id} as sent")

    logger.info("process_signals: All signals processed")

if __name__ == '__main__':
    conn = sqlite3.connect('database/stock_data.db')
    try:
        process_signals(conn)
    finally:
        conn.close()
        logger.info("Main script completed")
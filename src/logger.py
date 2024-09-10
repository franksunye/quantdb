import logging
import os

def setup_logger(log_name="quantdb", log_file="quantdb.log", level=logging.DEBUG):
    # 创建日志记录器
    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    # 创建日志文件夹，如果不存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 创建控制台处理器并设置级别
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # 创建文件处理器并设置级别
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # 将处理器添加到记录器
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

# 初始化日志记录器
logger = setup_logger(log_file="logs/quantdb.log")

# 示例：使用日志记录器
def example_function():
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.error("This is an error message")

if __name__ == "__main__":
    example_function()

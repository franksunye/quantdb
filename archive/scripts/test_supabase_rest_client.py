"""
测试 Supabase REST 客户端

此脚本用于测试 Supabase REST 客户端，使用 services/supabase_client.py 中的 SupabaseRestClient 类。
"""

import os
import sys
import logging
import traceback
import requests
from datetime import date
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_supabase_rest_client")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def test_supabase_rest_client():
    """测试 Supabase REST 客户端"""
    try:
        # 导入 SupabaseRestClient
        from services.supabase_client import SupabaseRestClient, get_supabase_client

        logger.info("创建 Supabase REST 客户端")

        # 创建客户端
        client = get_supabase_client()

        # 测试连接
        logger.info("测试连接")
        try:
            # 尝试获取服务器信息
            response = requests.get(
                f"{client.url}/rest/v1/",
                headers=client.headers
            )
            if response.status_code == 200:
                logger.info("连接成功")
            else:
                logger.error(f"连接失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

        # 检查表是否存在
        logger.info("检查表是否存在")
        try:
            # 执行SQL查询获取表列表
            sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public';
            """
            result = client.execute_sql(sql)
            tables = [row['table_name'] for row in result.get('data', [])]
            logger.info(f"表列表: {tables}")
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            tables = []
        logger.info(f"表列表: {tables}")

        # 如果表不存在，创建表
        if 'assets' not in tables:
            logger.info("创建 assets 表")

            # 创建 assets 表
            sql = """
            CREATE TABLE IF NOT EXISTS assets (
                asset_id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                isin VARCHAR(12),
                asset_type VARCHAR(20),
                exchange VARCHAR(20),
                currency VARCHAR(3),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol)
            );
            """

            result = client.execute_sql(sql)
            logger.info(f"创建 assets 表结果: {result}")

        if 'prices' not in tables:
            logger.info("创建 prices 表")

            # 创建 prices 表
            sql = """
            CREATE TABLE IF NOT EXISTS prices (
                price_id SERIAL PRIMARY KEY,
                asset_id INTEGER NOT NULL,
                date DATE NOT NULL,
                open NUMERIC(10, 2),
                high NUMERIC(10, 2),
                low NUMERIC(10, 2),
                close NUMERIC(10, 2),
                volume BIGINT,
                adjusted_close NUMERIC(10, 2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
                UNIQUE (asset_id, date)
            );
            """

            result = client.execute_sql(sql)
            logger.info(f"创建 prices 表结果: {result}")

            # 创建索引
            logger.info("创建索引")
            sql = """
            CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
            CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
            CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
            """

            result = client.execute_sql(sql)
            logger.info(f"创建索引结果: {result}")

        # 测试插入数据
        logger.info("测试插入数据")

        # 插入测试资产
        test_asset = {
            "symbol": f"TEST{date.today().strftime('%Y%m%d')}",
            "name": "测试资产",
            "asset_type": "STOCK",
            "exchange": "TEST",
            "currency": "CNY",
            "isin": f"CN{date.today().strftime('%Y%m%d')}"
        }

        # 插入资产
        try:
            result = client.insert("assets", test_asset)
            if result and isinstance(result, list) and len(result) > 0:
                asset_id = result[0].get('asset_id')
                logger.info(f"插入资产结果，ID: {asset_id}")
            else:
                logger.error(f"插入资产失败，结果: {result}")
                return False
        except Exception as e:
            logger.error(f"插入资产失败: {e}")
            return False

        if asset_id:
            # 插入测试价格
            test_price = {
                "asset_id": asset_id,
                "date": date.today().isoformat(),
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.5,
                "volume": 1000,
                "adjusted_close": 102.5
            }

            # 插入价格
            try:
                result = client.insert("prices", test_price)
                if result and isinstance(result, list) and len(result) > 0:
                    price_id = result[0].get('price_id')
                    logger.info(f"插入价格结果，ID: {price_id}")
                else:
                    logger.error(f"插入价格失败，结果: {result}")
                    return False
            except Exception as e:
                logger.error(f"插入价格失败: {e}")
                return False

            # 查询数据
            logger.info("查询数据")

            # 查询资产
            try:
                asset = client.select("assets", filters={"asset_id": asset_id})
                logger.info(f"查询资产结果: {asset}")
            except Exception as e:
                logger.error(f"查询资产失败: {e}")
                return False

            # 查询价格
            try:
                price = client.select("prices", filters={"price_id": price_id})
                logger.info(f"查询价格结果: {price}")
            except Exception as e:
                logger.error(f"查询价格失败: {e}")
                return False

            # 删除数据
            logger.info("删除数据")

            # 删除价格
            try:
                result = client.delete("prices", {"price_id": price_id})
                logger.info(f"删除价格结果: {result}")
            except Exception as e:
                logger.error(f"删除价格失败: {e}")
                return False

            # 删除资产
            try:
                result = client.delete("assets", {"asset_id": asset_id})
                logger.info(f"删除资产结果: {result}")
            except Exception as e:
                logger.error(f"删除资产失败: {e}")
                return False

        logger.info("Supabase REST 客户端测试成功")
        return True
    except Exception as e:
        logger.error(f"Supabase REST 客户端测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始测试 Supabase REST 客户端")

    # 测试 Supabase REST 客户端
    if not test_supabase_rest_client():
        logger.error("Supabase REST 客户端测试失败")
        return False

    logger.info("Supabase REST 客户端测试成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("脚本执行成功")
        sys.exit(0)
    else:
        logger.error("脚本执行失败")
        sys.exit(1)

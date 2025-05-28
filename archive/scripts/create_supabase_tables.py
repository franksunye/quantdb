"""
使用REST API创建Supabase表的脚本

此脚本使用Supabase的REST API创建必要的表。
"""

import sys
import requests
import json

def create_tables():
    """创建表"""
    try:
        # 从环境变量获取URL和密钥
        import os
        from dotenv import load_dotenv

        # 加载环境变量
        load_dotenv()

        # 获取URL和密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not supabase_url or not supabase_key or not supabase_service_key:
            print("未找到必要的Supabase环境变量")
            return False

        print(f"连接到Supabase: {supabase_url}")

        # 设置请求头
        headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }

        # 使用SQL API创建表
        # 注意：这需要service_role密钥

        # 创建assets表
        assets_sql = """
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

        print("创建assets表...")

        # 使用SQL API创建表
        # 注意：我们需要使用Supabase的SQL API，这通常是通过管理API提供的
        # 但是我们可以尝试使用REST API的rpc功能

        # 尝试使用REST API的rpc功能
        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                headers=headers,
                json={"sql": assets_sql}
            )

            if response.status_code == 200:
                print("assets表创建成功")
            else:
                print(f"assets表创建失败: {response.status_code} - {response.text}")
                print("尝试使用其他方法...")
        except Exception as e:
            print(f"使用REST API创建assets表失败: {e}")
            print("尝试使用其他方法...")

        # 创建prices表
        prices_sql = """
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

        print("创建prices表...")

        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                headers=headers,
                json={"sql": prices_sql}
            )

            if response.status_code == 200:
                print("prices表创建成功")
            else:
                print(f"prices表创建失败: {response.status_code} - {response.text}")
                print("尝试使用其他方法...")
        except Exception as e:
            print(f"使用REST API创建prices表失败: {e}")
            print("尝试使用其他方法...")

        # 创建索引
        indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
        CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
        CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
        """

        print("创建索引...")

        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/execute_sql",
                headers=headers,
                json={"sql": indexes_sql}
            )

            if response.status_code == 200:
                print("索引创建成功")
            else:
                print(f"索引创建失败: {response.status_code} - {response.text}")
                print("尝试使用其他方法...")
        except Exception as e:
            print(f"使用REST API创建索引失败: {e}")
            print("尝试使用其他方法...")

        # 检查表是否存在
        print("检查表是否存在...")

        # 设置请求头
        headers = {
            "apikey": supabase_key,
            "Content-Type": "application/json"
        }

        # 检查assets表
        print("检查assets表...")
        assets_response = requests.get(
            f"{supabase_url}/rest/v1/assets?limit=1",
            headers=headers
        )

        if assets_response.status_code == 200:
            print("assets表存在")
        else:
            print(f"assets表不存在: {assets_response.status_code} - {assets_response.text}")

        # 检查prices表
        print("检查prices表...")
        prices_response = requests.get(
            f"{supabase_url}/rest/v1/prices?limit=1",
            headers=headers
        )

        if prices_response.status_code == 200:
            print("prices表存在")
        else:
            print(f"prices表不存在: {prices_response.status_code} - {prices_response.text}")

        print("表创建尝试完成")
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        return False

def main():
    """主函数"""
    print("开始创建Supabase表")

    # 创建表
    if not create_tables():
        print("创建表失败")
        return False

    print("Supabase表创建尝试完成")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("脚本执行完成")
        sys.exit(0)
    else:
        print("脚本执行失败")
        sys.exit(1)

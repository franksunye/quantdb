"""
使用Supabase Management API创建表的脚本

此脚本使用Supabase Management API创建必要的表。
"""

import os
import sys
import requests
from dotenv import load_dotenv

def create_tables():
    """创建表"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取Supabase URL和API密钥
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key or not supabase_service_key:
            print("未找到必要的Supabase环境变量")
            return False
        
        # 获取项目ID
        project_id = supabase_url.split('//')[1].split('.')[0]
        
        print(f"项目ID: {project_id}")
        print(f"连接到Supabase: {supabase_url}")
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json"
        }
        
        # SQL查询
        sql = """
        -- 创建assets表
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
        
        -- 创建prices表
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
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_prices_asset_id ON prices (asset_id);
        CREATE INDEX IF NOT EXISTS idx_prices_date ON prices (date);
        CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
        """
        
        # 使用Management API执行SQL查询
        print("执行SQL查询...")
        
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{project_id}/sql",
            headers=headers,
            json={"query": sql}
        )
        
        if response.status_code == 200:
            print("SQL查询执行成功")
            print(f"响应: {response.json()}")
        else:
            print(f"SQL查询执行失败: {response.status_code} - {response.text}")
            return False
        
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
            return False
        
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
            return False
        
        print("表创建成功")
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
    
    print("Supabase表创建成功")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("脚本执行成功")
        sys.exit(0)
    else:
        print("脚本执行失败")
        sys.exit(1)

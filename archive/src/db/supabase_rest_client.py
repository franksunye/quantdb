"""
Supabase REST Client

这个模块提供了一个基于REST API的Supabase客户端，用于解决中文Windows环境下的编码问题。
通过使用REST API而不是直接的数据库连接，我们可以避免psycopg2在中文Windows环境下的编码问题。
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase-rest-client")

class SupabaseRestClient:
    """Supabase REST API客户端"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, supabase_service_key: str = None):
        """
        初始化Supabase REST客户端
        
        Args:
            supabase_url: Supabase项目URL
            supabase_key: Supabase匿名密钥
            supabase_service_key: Supabase服务角色密钥
        """
        # 加载环境变量
        load_dotenv()
        
        # 设置Supabase URL和密钥
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        self.supabase_service_key = supabase_service_key or os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL和密钥必须提供。请设置SUPABASE_URL和SUPABASE_KEY环境变量或通过参数传递。")
        
        # 设置REST API基础URL
        self.rest_url = f"{self.supabase_url}/rest/v1"
        
        # 设置请求头
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # 设置服务角色请求头（用于需要更高权限的操作）
        self.service_headers = {
            "apikey": self.supabase_service_key,
            "Authorization": f"Bearer {self.supabase_service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        logger.info(f"Supabase REST客户端初始化完成，URL: {self.supabase_url}")
    
    def _handle_response(self, response: requests.Response, operation: str) -> Any:
        """
        处理API响应
        
        Args:
            response: 响应对象
            operation: 操作名称
        
        Returns:
            处理后的响应数据
        
        Raises:
            Exception: 如果响应状态码不成功
        """
        if response.status_code in (200, 201, 204):
            if response.status_code == 204 or not response.text:
                return None
            return response.json()
        else:
            error_message = f"{operation}失败: {response.status_code} - {response.text}"
            logger.error(error_message)
            raise Exception(error_message)
    
    def _json_serial(self, obj):
        """处理JSON序列化中的特殊类型"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"无法序列化类型 {type(obj)}")
    
    def select(self, table: str, columns: str = "*", filters: Dict = None, order: str = None, limit: int = None) -> List[Dict]:
        """
        从表中选择数据
        
        Args:
            table: 表名
            columns: 要选择的列，默认为所有列
            filters: 过滤条件
            order: 排序条件
            limit: 限制返回的行数
        
        Returns:
            查询结果列表
        """
        url = f"{self.rest_url}/{table}"
        params = {}
        
        # 添加列选择
        if columns and columns != "*":
            params["select"] = columns
        
        # 添加过滤条件
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    # 处理IN查询
                    operator, values = value
                    if operator.lower() == "in":
                        params[f"{key}"] = f"in.({','.join(map(str, values))})"
                    elif operator.lower() == "not.in":
                        params[f"{key}"] = f"not.in.({','.join(map(str, values))})"
                else:
                    # 处理简单条件
                    params[key] = f"eq.{value}"
        
        # 添加排序条件
        if order:
            params["order"] = order
        
        # 添加限制
        if limit:
            params["limit"] = limit
        
        # 发送请求
        logger.debug(f"发送请求: GET {url} 参数: {params}")
        response = requests.get(url, headers=self.headers, params=params)
        
        return self._handle_response(response, f"从表 {table} 中选择数据")
    
    def insert(self, table: str, data: Union[Dict, List[Dict]]) -> Any:
        """
        向表中插入数据
        
        Args:
            table: 表名
            data: 要插入的数据，可以是单个字典或字典列表
        
        Returns:
            插入的数据
        """
        url = f"{self.rest_url}/{table}"
        
        # 确保数据是JSON可序列化的
        if isinstance(data, list):
            json_data = json.dumps(data, default=self._json_serial)
        else:
            json_data = json.dumps([data], default=self._json_serial)
        
        # 发送请求
        logger.debug(f"发送请求: POST {url} 数据: {json_data}")
        response = requests.post(url, headers=self.headers, data=json_data)
        
        return self._handle_response(response, f"向表 {table} 中插入数据")
    
    def update(self, table: str, data: Dict, filters: Dict) -> Any:
        """
        更新表中的数据
        
        Args:
            table: 表名
            data: 要更新的数据
            filters: 过滤条件
        
        Returns:
            更新后的数据
        """
        url = f"{self.rest_url}/{table}"
        params = {}
        
        # 添加过滤条件
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        
        # 确保数据是JSON可序列化的
        json_data = json.dumps(data, default=self._json_serial)
        
        # 发送请求
        logger.debug(f"发送请求: PATCH {url} 参数: {params} 数据: {json_data}")
        response = requests.patch(url, headers=self.headers, params=params, data=json_data)
        
        return self._handle_response(response, f"更新表 {table} 中的数据")
    
    def delete(self, table: str, filters: Dict) -> Any:
        """
        删除表中的数据
        
        Args:
            table: 表名
            filters: 过滤条件
        
        Returns:
            删除的数据
        """
        url = f"{self.rest_url}/{table}"
        params = {}
        
        # 添加过滤条件
        for key, value in filters.items():
            params[key] = f"eq.{value}"
        
        # 发送请求
        logger.debug(f"发送请求: DELETE {url} 参数: {params}")
        response = requests.delete(url, headers=self.headers, params=params)
        
        return self._handle_response(response, f"删除表 {table} 中的数据")
    
    def execute_sql(self, query: str, params: Dict = None) -> Any:
        """
        执行SQL查询（需要服务角色密钥）
        
        Args:
            query: SQL查询
            params: 查询参数
        
        Returns:
            查询结果
        """
        if not self.supabase_service_key:
            raise ValueError("执行SQL查询需要服务角色密钥。请设置SUPABASE_SERVICE_KEY环境变量或通过参数传递。")
        
        url = f"{self.supabase_url}/rest/v1/rpc/exec_sql"
        
        # 准备请求数据
        data = {
            "query": query
        }
        
        if params:
            data["params"] = params
        
        # 发送请求
        logger.debug(f"发送请求: POST {url} 数据: {data}")
        response = requests.post(url, headers=self.service_headers, json=data)
        
        return self._handle_response(response, "执行SQL查询")
    
    def rpc(self, function: str, params: Dict = None) -> Any:
        """
        调用存储过程
        
        Args:
            function: 存储过程名称
            params: 存储过程参数
        
        Returns:
            存储过程结果
        """
        url = f"{self.rest_url}/rpc/{function}"
        
        # 准备请求数据
        data = params or {}
        
        # 发送请求
        logger.debug(f"发送请求: POST {url} 数据: {data}")
        response = requests.post(url, headers=self.headers, json=data)
        
        return self._handle_response(response, f"调用存储过程 {function}")

# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    client = SupabaseRestClient()
    
    # 查询示例
    assets = client.select("assets", limit=5)
    print(f"资产: {assets}")
    
    # 插入示例
    new_asset = {
        "symbol": "TEST",
        "name": "测试资产",
        "asset_type": "stock",
        "exchange": "TEST",
        "is_active": True
    }
    result = client.insert("assets", new_asset)
    print(f"插入结果: {result}")
    
    # 更新示例
    update_result = client.update("assets", {"is_active": False}, {"symbol": "TEST"})
    print(f"更新结果: {update_result}")
    
    # 删除示例
    delete_result = client.delete("assets", {"symbol": "TEST"})
    print(f"删除结果: {delete_result}")

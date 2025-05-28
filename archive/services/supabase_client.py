"""
Supabase REST API客户端

此模块提供了一个基于REST API的Supabase客户端，用于在中文Windows环境下避免编码问题。
"""

import os
import json
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# 设置日志
logger = logging.getLogger(__name__)

class SupabaseRestClient:
    """Supabase REST API客户端"""
    
    def __init__(self, url: str = None, key: str = None, service_key: str = None):
        """
        初始化Supabase REST API客户端
        
        Args:
            url: Supabase URL，如果为None则从环境变量获取
            key: Supabase anon key，如果为None则从环境变量获取
            service_key: Supabase service role key，如果为None则从环境变量获取
        """
        # 加载环境变量
        load_dotenv()
        
        # 设置URL和密钥
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        self.service_key = service_key or os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("未找到Supabase URL或API密钥，请检查环境变量或提供参数")
        
        # 设置请求头
        self.headers = {
            "apikey": self.key,
            "Content-Type": "application/json"
        }
        
        self.service_headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json"
        } if self.service_key else None
        
        logger.info(f"初始化Supabase客户端: {self.url}")
    
    def _handle_response(self, response: requests.Response, operation: str) -> Any:
        """
        处理API响应
        
        Args:
            response: 响应对象
            operation: 操作名称
        
        Returns:
            处理后的响应数据
        
        Raises:
            Exception: 如果响应状态码不是成功状态
        """
        if response.status_code in (200, 201, 204):
            if response.status_code == 204 or not response.text:
                return None
            return response.json()
        else:
            error_message = f"{operation}失败: {response.status_code} - {response.text}"
            logger.error(error_message)
            raise Exception(error_message)
    
    def _build_query_url(self, table: str, filters: Dict = None, limit: int = None, 
                         order: str = None, offset: int = None) -> str:
        """
        构建查询URL
        
        Args:
            table: 表名
            filters: 过滤条件
            limit: 限制返回的记录数
            order: 排序条件
            offset: 偏移量
        
        Returns:
            查询URL
        """
        query_url = f"{self.url}/rest/v1/{table}"
        query_params = []
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    # 处理in查询
                    values_str = ",".join([str(v) for v in value])
                    query_params.append(f"{key}=in.({values_str})")
                else:
                    # 处理eq查询
                    query_params.append(f"{key}=eq.{value}")
        
        if limit:
            query_params.append(f"limit={limit}")
        
        if order:
            query_params.append(f"order={order}")
        
        if offset:
            query_params.append(f"offset={offset}")
        
        if query_params:
            query_url += "?" + "&".join(query_params)
        
        return query_url
    
    def select(self, table: str, columns: str = "*", filters: Dict = None, 
               limit: int = None, order: str = None, offset: int = None) -> List[Dict]:
        """
        查询数据
        
        Args:
            table: 表名
            columns: 要查询的列，默认为所有列
            filters: 过滤条件
            limit: 限制返回的记录数
            order: 排序条件
            offset: 偏移量
        
        Returns:
            查询结果列表
        """
        query_url = self._build_query_url(table, filters, limit, order, offset)
        query_url += f"&select={columns}" if "?" in query_url else f"?select={columns}"
        
        logger.debug(f"查询URL: {query_url}")
        
        response = requests.get(query_url, headers=self.headers)
        return self._handle_response(response, "查询")
    
    def insert(self, table: str, data: Union[Dict, List[Dict]], 
               upsert: bool = False) -> Dict:
        """
        插入数据
        
        Args:
            table: 表名
            data: 要插入的数据，可以是单个字典或字典列表
            upsert: 是否使用upsert模式（如果记录已存在则更新）
        
        Returns:
            插入的数据
        """
        query_url = f"{self.url}/rest/v1/{table}"
        
        if upsert:
            query_url += "?on_conflict=id"
        
        headers = self.headers.copy()
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates"
        
        logger.debug(f"插入URL: {query_url}")
        logger.debug(f"插入数据: {data}")
        
        response = requests.post(query_url, headers=headers, json=data)
        return self._handle_response(response, "插入")
    
    def update(self, table: str, data: Dict, filters: Dict) -> Dict:
        """
        更新数据
        
        Args:
            table: 表名
            data: 要更新的数据
            filters: 过滤条件
        
        Returns:
            更新的数据
        """
        query_url = self._build_query_url(table, filters)
        
        logger.debug(f"更新URL: {query_url}")
        logger.debug(f"更新数据: {data}")
        
        response = requests.patch(query_url, headers=self.headers, json=data)
        return self._handle_response(response, "更新")
    
    def delete(self, table: str, filters: Dict) -> None:
        """
        删除数据
        
        Args:
            table: 表名
            filters: 过滤条件
        
        Returns:
            None
        """
        query_url = self._build_query_url(table, filters)
        
        logger.debug(f"删除URL: {query_url}")
        
        response = requests.delete(query_url, headers=self.headers)
        return self._handle_response(response, "删除")
    
    def execute_batch(self, operations: List[Dict]) -> List[Any]:
        """
        批量执行操作
        
        Args:
            operations: 操作列表，每个操作是一个字典，包含method、table、data等字段
        
        Returns:
            操作结果列表
        """
        results = []
        
        for op in operations:
            method = op.get("method", "").lower()
            table = op.get("table", "")
            data = op.get("data", {})
            filters = op.get("filters", {})
            
            if not method or not table:
                raise ValueError(f"无效的操作: {op}")
            
            try:
                if method == "select":
                    columns = op.get("columns", "*")
                    limit = op.get("limit")
                    order = op.get("order")
                    offset = op.get("offset")
                    result = self.select(table, columns, filters, limit, order, offset)
                elif method == "insert":
                    upsert = op.get("upsert", False)
                    result = self.insert(table, data, upsert)
                elif method == "update":
                    result = self.update(table, data, filters)
                elif method == "delete":
                    result = self.delete(table, filters)
                else:
                    raise ValueError(f"不支持的方法: {method}")
                
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        return results
    
    def execute_sql(self, sql: str, params: Dict = None) -> Dict:
        """
        执行SQL查询（需要service_role权限）
        
        Args:
            sql: SQL查询
            params: 查询参数
        
        Returns:
            查询结果
        """
        if not self.service_key:
            raise ValueError("执行SQL查询需要service_role密钥")
        
        # 获取项目ID
        project_id = self.url.split('//')[1].split('.')[0]
        
        # 构建请求
        url = f"https://api.supabase.com/v1/projects/{project_id}/sql"
        data = {"query": sql}
        
        if params:
            data["params"] = params
        
        logger.debug(f"执行SQL: {sql}")
        
        response = requests.post(url, headers=self.service_headers, json=data)
        return self._handle_response(response, "执行SQL")
    
    def get_table_definition(self, table: str) -> Dict:
        """
        获取表定义（需要service_role权限）
        
        Args:
            table: 表名
        
        Returns:
            表定义
        """
        sql = f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM 
            information_schema.columns
        WHERE 
            table_name = '{table}'
        ORDER BY 
            ordinal_position;
        """
        
        return self.execute_sql(sql)
    
    def create_table(self, table: str, columns: Dict[str, str], 
                     primary_key: str = None, if_not_exists: bool = True) -> Dict:
        """
        创建表（需要service_role权限）
        
        Args:
            table: 表名
            columns: 列定义，键为列名，值为列类型
            primary_key: 主键列名
            if_not_exists: 是否使用IF NOT EXISTS子句
        
        Returns:
            执行结果
        """
        # 构建列定义
        column_defs = []
        for name, type_def in columns.items():
            column_defs.append(f"{name} {type_def}")
        
        # 添加主键定义
        if primary_key:
            column_defs.append(f"PRIMARY KEY ({primary_key})")
        
        # 构建SQL
        sql = f"CREATE TABLE {'IF NOT EXISTS ' if if_not_exists else ''}{table} (\n"
        sql += ",\n".join(column_defs)
        sql += "\n);"
        
        return self.execute_sql(sql)
    
    def create_index(self, table: str, columns: List[str], 
                     name: str = None, unique: bool = False, 
                     if_not_exists: bool = True) -> Dict:
        """
        创建索引（需要service_role权限）
        
        Args:
            table: 表名
            columns: 索引列
            name: 索引名称
            unique: 是否是唯一索引
            if_not_exists: 是否使用IF NOT EXISTS子句
        
        Returns:
            执行结果
        """
        # 生成索引名称
        if not name:
            name = f"idx_{table}_{'_'.join(columns)}"
        
        # 构建SQL
        sql = f"CREATE {'UNIQUE ' if unique else ''}INDEX "
        sql += f"{'IF NOT EXISTS ' if if_not_exists else ''}{name} "
        sql += f"ON {table} ({', '.join(columns)});"
        
        return self.execute_sql(sql)

# 单例模式
_instance = None

def get_supabase_client() -> SupabaseRestClient:
    """
    获取Supabase客户端单例
    
    Returns:
        Supabase客户端实例
    """
    global _instance
    if _instance is None:
        _instance = SupabaseRestClient()
    return _instance

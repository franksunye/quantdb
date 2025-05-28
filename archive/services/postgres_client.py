"""
PostgreSQL 直连客户端

此模块提供了直接连接 PostgreSQL 数据库的功能，特别针对 Supabase PostgreSQL 数据库。
解决了中文 Windows 环境下的编码问题。
"""

import os
import logging
import urllib.parse
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
from dotenv import load_dotenv

# 设置日志
logger = logging.getLogger(__name__)

class PostgresClient:
    """PostgreSQL 直连客户端"""
    
    def __init__(self, host: str = None, port: int = None, 
                 dbname: str = None, user: str = None, password: str = None,
                 sslmode: str = "require"):
        """
        初始化 PostgreSQL 直连客户端
        
        Args:
            host: 数据库主机，如果为 None 则从环境变量获取
            port: 数据库端口，如果为 None 则从环境变量获取或使用默认值 5432
            dbname: 数据库名称，如果为 None 则从环境变量获取或使用默认值 postgres
            user: 数据库用户名，如果为 None 则从环境变量获取或使用默认值 postgres
            password: 数据库密码，如果为 None 则从环境变量获取
            sslmode: SSL 模式，默认为 require
        """
        # 加载环境变量
        load_dotenv()
        
        # 设置连接参数
        self.host = host or os.getenv('SUPABASE_DB_HOST') or "db.dvusiqfijdmjcsubyapw.supabase.co"
        self.port = port or int(os.getenv('SUPABASE_DB_PORT') or 5432)
        self.dbname = dbname or os.getenv('SUPABASE_DB_NAME') or "postgres"
        self.user = user or os.getenv('SUPABASE_DB_USER') or "postgres"
        self.password = password or os.getenv('SUPABASE_DB_PASSWORD')
        self.sslmode = sslmode
        
        if not self.password:
            self.password = os.getenv('SUPABASE_DB_PASSWORD')
            
        if not self.password:
            raise ValueError("未找到数据库密码，请检查环境变量或提供参数")
        
        # 记录连接信息（不包含密码）
        logger.info(f"初始化 PostgreSQL 客户端: {self.host}:{self.port}/{self.dbname} (用户: {self.user})")
        
        # 导入 psycopg2，如果不可用则尝试导入 pg8000
        try:
            import psycopg2
            self.driver = "psycopg2"
            logger.info("使用 psycopg2 驱动")
        except ImportError:
            try:
                import pg8000
                self.driver = "pg8000"
                logger.info("使用 pg8000 驱动")
            except ImportError:
                raise ImportError("未找到 PostgreSQL 驱动，请安装 psycopg2 或 pg8000")
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接
        
        Returns:
            数据库连接对象
        """
        conn = None
        try:
            if self.driver == "psycopg2":
                import psycopg2
                # 使用显式参数连接，避免编码问题
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    sslmode=self.sslmode
                )
            else:  # pg8000
                import pg8000
                conn = pg8000.connect(
                    host=self.host,
                    port=self.port,
                    database=self.dbname,
                    user=self.user,
                    password=self.password,
                    ssl=True if self.sslmode == "require" else False
                )
            
            # 设置客户端编码为 UTF-8
            if self.driver == "psycopg2":
                conn.set_client_encoding('UTF8')
            
            yield conn
        except Exception as e:
            logger.error(f"获取数据库连接失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("数据库连接已关闭")
    
    @contextmanager
    def get_cursor(self, commit=True):
        """
        获取数据库游标
        
        Args:
            commit: 是否在操作完成后提交事务
        
        Returns:
            数据库游标对象
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"数据库操作失败: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """
        执行查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果列表
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_query_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """
        执行查询并返回一条结果
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果，如果没有结果则返回 None
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    
    def execute_query_scalar(self, query: str, params: tuple = None) -> Any:
        """
        执行查询并返回单个值
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果的第一个字段，如果没有结果则返回 None
        """
        result = self.execute_query_one(query, params)
        return result[0] if result else None
    
    def execute_query_dict(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询并返回字典列表
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果的字典列表
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params or ())
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            
            # 转换为字典列表
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_query_dict_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """
        执行查询并返回一个字典
        
        Args:
            query: SQL 查询语句
            params: 查询参数
        
        Returns:
            查询结果的字典，如果没有结果则返回 None
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params or ())
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            
            # 获取一行结果
            row = cursor.fetchone()
            
            # 转换为字典
            return dict(zip(columns, row)) if row else None
    
    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """
        执行非查询操作
        
        Args:
            query: SQL 语句
            params: 查询参数
        
        Returns:
            受影响的行数
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
    
    def insert(self, table: str, data: Dict) -> int:
        """
        插入数据
        
        Args:
            table: 表名
            data: 要插入的数据
        
        Returns:
            插入的行 ID
        """
        # 构建 SQL
        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)
        values = [data[column] for column in columns]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        
        # 执行插入
        return self.execute_query_scalar(query, tuple(values))
    
    def update(self, table: str, data: Dict, condition: str, params: tuple = None) -> int:
        """
        更新数据
        
        Args:
            table: 表名
            data: 要更新的数据
            condition: 更新条件
            params: 条件参数
        
        Returns:
            受影响的行数
        """
        # 构建 SQL
        set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
        values = list(data.values())
        
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        
        # 执行更新
        return self.execute_non_query(query, tuple(values) + (params or ()))
    
    def delete(self, table: str, condition: str, params: tuple = None) -> int:
        """
        删除数据
        
        Args:
            table: 表名
            condition: 删除条件
            params: 条件参数
        
        Returns:
            受影响的行数
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_non_query(query, params)
    
    def table_exists(self, table: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table: 表名
        
        Returns:
            表是否存在
        """
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
        """
        return self.execute_query_scalar(query, (table,))
    
    def get_table_columns(self, table: str) -> List[str]:
        """
        获取表的列名
        
        Args:
            table: 表名
        
        Returns:
            列名列表
        """
        query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position
        """
        return [row[0] for row in self.execute_query(query, (table,))]

# 单例模式
_instance = None

def get_postgres_client() -> PostgresClient:
    """
    获取 PostgreSQL 客户端单例
    
    Returns:
        PostgreSQL 客户端实例
    """
    global _instance
    if _instance is None:
        _instance = PostgresClient()
    return _instance

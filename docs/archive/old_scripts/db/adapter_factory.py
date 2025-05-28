#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库适配器工厂
用于创建适当的数据库适配器实例
"""

import os
import logging
from typing import Optional, Union, TYPE_CHECKING
from dotenv import load_dotenv

if TYPE_CHECKING:
    from src.db.supabase_adapter import SupabaseAdapter
    from src.db.sqlite_adapter import SQLiteAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("adapter_factory")

# 从.env文件加载环境变量
load_dotenv()

# 从配置中获取数据库类型
from src.config import DB_TYPE

def create_db_adapter(adapter_type: Optional[str] = None) -> Union['SupabaseAdapter', 'SQLiteAdapter']:
    """
    创建数据库适配器实例

    Args:
        adapter_type: 适配器类型，可选值为 'supabase' 或 'sqlite'，
                     如果为None，则根据配置的DB_TYPE自动选择

    Returns:
        数据库适配器实例
    """
    # 如果未指定适配器类型，则使用配置中的DB_TYPE
    if adapter_type is None:
        adapter_type = DB_TYPE

    logger.info(f"创建数据库适配器: {adapter_type}")

    if adapter_type.lower() == 'supabase':
        from src.db.supabase_adapter import SupabaseAdapter
        return SupabaseAdapter()
    else:
        from src.db.sqlite_adapter import SQLiteAdapter
        return SQLiteAdapter()

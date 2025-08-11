"""
QDB专用测试配置文件
避免与主conftest.py的依赖冲突
"""

import pytest
import tempfile
import shutil
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_cache_dir():
    """创建临时缓存目录"""
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, "test_cache")
    yield cache_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def reset_qdb_client():
    """重置QDB全局客户端"""
    import qdb.client

    original_client = qdb.client._global_client
    qdb.client._global_client = None
    yield
    qdb.client._global_client = original_client

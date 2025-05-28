"""
测试Supabase REST API客户端

此脚本用于测试基于REST API的Supabase客户端。
"""

import os
import sys
import logging
import unittest
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入Supabase客户端
from services.supabase_client import SupabaseRestClient, get_supabase_client

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_supabase_client")

class TestSupabaseClient(unittest.TestCase):
    """测试Supabase REST API客户端"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建Supabase客户端
        cls.client = get_supabase_client()
        
        # 测试表名
        cls.test_table = "test_assets"
        
        # 创建测试表
        try:
            cls.client.execute_sql(f"""
            CREATE TABLE IF NOT EXISTS {cls.test_table} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                value NUMERIC(10, 2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)
            logger.info(f"创建测试表: {cls.test_table}")
        except Exception as e:
            logger.warning(f"创建测试表失败: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        # 删除测试表
        try:
            cls.client.execute_sql(f"DROP TABLE IF EXISTS {cls.test_table};")
            logger.info(f"删除测试表: {cls.test_table}")
        except Exception as e:
            logger.warning(f"删除测试表失败: {e}")
    
    def setUp(self):
        """每个测试前的设置"""
        # 清空测试表
        try:
            self.client.execute_sql(f"DELETE FROM {self.test_table};")
            logger.info(f"清空测试表: {self.test_table}")
        except Exception as e:
            logger.warning(f"清空测试表失败: {e}")
    
    def test_connection(self):
        """测试连接"""
        # 测试连接
        try:
            # 执行简单查询
            result = self.client.select(self.test_table)
            self.assertIsInstance(result, list)
            logger.info("连接测试通过")
        except Exception as e:
            self.fail(f"连接测试失败: {e}")
    
    def test_insert(self):
        """测试插入数据"""
        # 插入数据
        test_data = {
            "name": "测试资产",
            "value": 100.50
        }
        
        try:
            result = self.client.insert(self.test_table, test_data)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["name"], test_data["name"])
            self.assertEqual(float(result["value"]), test_data["value"])
            self.assertIn("id", result)
            logger.info(f"插入数据成功: {result}")
            
            # 验证数据已插入
            inserted = self.client.select(self.test_table, filters={"id": result["id"]})
            self.assertEqual(len(inserted), 1)
            self.assertEqual(inserted[0]["name"], test_data["name"])
            
            return result["id"]  # 返回插入的ID，供其他测试使用
        except Exception as e:
            self.fail(f"插入数据测试失败: {e}")
    
    def test_update(self):
        """测试更新数据"""
        # 先插入数据
        id = self.test_insert()
        
        # 更新数据
        update_data = {
            "name": "更新后的资产",
            "value": 200.75
        }
        
        try:
            result = self.client.update(self.test_table, update_data, {"id": id})
            self.assertIsInstance(result, dict)
            logger.info(f"更新数据成功: {result}")
            
            # 验证数据已更新
            updated = self.client.select(self.test_table, filters={"id": id})
            self.assertEqual(len(updated), 1)
            self.assertEqual(updated[0]["name"], update_data["name"])
            self.assertEqual(float(updated[0]["value"]), update_data["value"])
        except Exception as e:
            self.fail(f"更新数据测试失败: {e}")
    
    def test_delete(self):
        """测试删除数据"""
        # 先插入数据
        id = self.test_insert()
        
        # 删除数据
        try:
            self.client.delete(self.test_table, {"id": id})
            logger.info(f"删除数据成功: id={id}")
            
            # 验证数据已删除
            deleted = self.client.select(self.test_table, filters={"id": id})
            self.assertEqual(len(deleted), 0)
        except Exception as e:
            self.fail(f"删除数据测试失败: {e}")
    
    def test_batch_operations(self):
        """测试批量操作"""
        # 定义批量操作
        operations = [
            {
                "method": "insert",
                "table": self.test_table,
                "data": {"name": "批量操作1", "value": 101.01}
            },
            {
                "method": "insert",
                "table": self.test_table,
                "data": {"name": "批量操作2", "value": 202.02}
            },
            {
                "method": "select",
                "table": self.test_table,
                "filters": {"name": "批量操作1"}
            }
        ]
        
        try:
            results = self.client.execute_batch(operations)
            self.assertEqual(len(results), 3)
            self.assertTrue(results[0]["success"])
            self.assertTrue(results[1]["success"])
            self.assertTrue(results[2]["success"])
            
            # 验证插入和查询结果
            self.assertEqual(results[0]["data"]["name"], "批量操作1")
            self.assertEqual(results[1]["data"]["name"], "批量操作2")
            self.assertEqual(len(results[2]["data"]), 1)
            self.assertEqual(results[2]["data"][0]["name"], "批量操作1")
            
            logger.info(f"批量操作测试成功: {results}")
        except Exception as e:
            self.fail(f"批量操作测试失败: {e}")
    
    def test_sql_execution(self):
        """测试SQL执行"""
        try:
            # 执行SQL插入
            sql = f"""
            INSERT INTO {self.test_table} (name, value)
            VALUES ('SQL测试', 123.45)
            RETURNING *;
            """
            
            result = self.client.execute_sql(sql)
            self.assertIsInstance(result, dict)
            self.assertIn("data", result)
            self.assertIsInstance(result["data"], list)
            self.assertGreater(len(result["data"]), 0)
            
            # 验证数据已插入
            inserted = self.client.select(self.test_table, filters={"name": "SQL测试"})
            self.assertEqual(len(inserted), 1)
            self.assertEqual(float(inserted[0]["value"]), 123.45)
            
            logger.info(f"SQL执行测试成功: {result}")
        except Exception as e:
            self.fail(f"SQL执行测试失败: {e}")

def run_all_tests():
    """运行所有测试"""
    logger.info("开始测试Supabase REST API客户端")
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSupabaseClient))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 检查结果
    if result.wasSuccessful():
        logger.info("所有测试通过")
        return True
    else:
        logger.error(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

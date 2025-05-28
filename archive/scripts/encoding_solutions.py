"""
Supabase编码问题解决方案

此脚本提供了多种解决中文Windows环境下Supabase连接编码问题的方法。
"""

import os
import sys
import logging
import urllib.parse
import traceback
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/encoding_solutions.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("encoding_solutions")

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 加载环境变量
load_dotenv()

class EncodingMiddleware:
    """编码转换中间层"""
    
    @staticmethod
    def convert_encoding(text, source_encoding='cp936', target_encoding='utf-8'):
        """将字符串从源编码转换为目标编码"""
        try:
            # 如果text已经是bytes类型，直接解码
            if isinstance(text, bytes):
                return text.decode(target_encoding)
            
            # 否则先编码再解码
            return text.encode(source_encoding).decode(target_encoding)
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logger.error(f"编码转换失败: {e}")
            return text
    
    @staticmethod
    def url_encode_password(password):
        """URL编码密码"""
        try:
            return urllib.parse.quote(password)
        except Exception as e:
            logger.error(f"URL编码密码失败: {e}")
            return password
    
    @staticmethod
    def parse_db_url_safe(database_url):
        """安全解析数据库URL，处理特殊字符"""
        try:
            # 解析URL
            if database_url.startswith('postgresql://'):
                # 分离用户名密码部分和主机部分
                auth_host_parts = database_url.replace('postgresql://', '').split('@', 1)
                
                if len(auth_host_parts) != 2:
                    raise ValueError("数据库URL格式错误，缺少@符号")
                
                auth_part = auth_host_parts[0]
                host_part = auth_host_parts[1]
                
                # 分离用户名和密码
                if ':' in auth_part:
                    user, password = auth_part.split(':', 1)
                    # URL解码密码，处理特殊字符
                    password = urllib.parse.unquote(password)
                else:
                    user = auth_part
                    password = ''
                
                # 分离主机和数据库名
                if '/' in host_part:
                    host_port, dbname = host_part.split('/', 1)
                else:
                    host_port = host_part
                    dbname = ''
                
                # 分离主机和端口
                if ':' in host_port:
                    host, port_str = host_port.split(':', 1)
                    port = int(port_str)
                else:
                    host = host_port
                    port = 5432
                
                return {
                    'dbname': dbname,
                    'user': user,
                    'password': password,
                    'host': host,
                    'port': port
                }
            else:
                raise ValueError(f"不支持的数据库URL格式: {database_url}")
        except Exception as e:
            logger.error(f"解析数据库URL失败: {e}")
            raise

class Solution1_EncodingMiddleware:
    """解决方案1：使用编码转换中间层"""
    
    @staticmethod
    def connect_to_supabase_db():
        """使用编码转换中间层连接到Supabase数据库"""
        try:
            import psycopg2
            
            # 获取数据库URL
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("未找到DATABASE_URL环境变量")
                return False
            
            # 安全解析数据库URL
            try:
                db_params = EncodingMiddleware.parse_db_url_safe(database_url)
                
                # 打印连接信息（隐藏密码）
                logger.info(f"连接到PostgreSQL数据库: {db_params['host']}:{db_params['port']}/{db_params['dbname']} (用户: {db_params['user']})")
                
                # 对密码进行编码转换
                original_password = db_params['password']
                converted_password = EncodingMiddleware.convert_encoding(original_password)
                
                logger.info(f"原始密码长度: {len(original_password)}")
                logger.info(f"转换后密码长度: {len(converted_password)}")
                
                # 连接到数据库
                conn = psycopg2.connect(
                    dbname=db_params['dbname'],
                    user=db_params['user'],
                    password=converted_password,
                    host=db_params['host'],
                    port=db_params['port']
                )
                
                logger.info("数据库连接成功")
                
                # 测试连接
                cur = conn.cursor()
                cur.execute("SELECT version()")
                version = cur.fetchone()
                
                logger.info(f"PostgreSQL版本: {version[0]}")
                
                # 关闭连接
                cur.close()
                conn.close()
                
                return True
            except Exception as e:
                logger.error(f"解析数据库URL或连接失败: {e}")
                logger.error(traceback.format_exc())
                return False
        except ImportError:
            logger.error("psycopg2未安装")
            return False

class Solution2_DirectParameters:
    """解决方案2：直接使用连接参数"""
    
    @staticmethod
    def connect_to_supabase_db():
        """直接使用连接参数连接到Supabase数据库"""
        try:
            import psycopg2
            
            # 直接使用连接参数
            db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
            db_port = 5432
            db_name = "postgres"
            db_user = "postgres"
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            
            if not db_password:
                logger.error("未找到SUPABASE_DB_PASSWORD环境变量")
                return False
            
            logger.info(f"连接到PostgreSQL数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
            
            # 连接到数据库
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            
            logger.info("数据库连接成功")
            
            # 测试连接
            cur = conn.cursor()
            cur.execute("SELECT version()")
            version = cur.fetchone()
            
            logger.info(f"PostgreSQL版本: {version[0]}")
            
            # 关闭连接
            cur.close()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            logger.error(traceback.format_exc())
            return False

class Solution3_RestAPI:
    """解决方案3：使用REST API"""
    
    @staticmethod
    def connect_to_supabase_api():
        """使用REST API连接到Supabase"""
        try:
            import requests
            
            # 获取Supabase URL和API密钥
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                logger.error("未找到必要的Supabase环境变量")
                return False
            
            logger.info(f"连接到Supabase API: {supabase_url}")
            
            # 设置请求头
            headers = {
                "apikey": supabase_key,
                "Content-Type": "application/json"
            }
            
            # 测试连接
            response = requests.get(
                f"{supabase_url}/rest/v1/",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Supabase API连接成功")
                logger.info(f"响应状态码: {response.status_code}")
                logger.info(f"响应内容: {response.text[:100]}...")
                return True
            else:
                logger.error(f"Supabase API连接失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Supabase API连接失败: {e}")
            logger.error(traceback.format_exc())
            return False

class Solution4_AlternativeClient:
    """解决方案4：使用替代PostgreSQL客户端"""
    
    @staticmethod
    def connect_with_pg8000():
        """使用pg8000连接到Supabase数据库"""
        try:
            import pg8000
            
            # 获取数据库连接参数
            db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
            db_port = 5432
            db_name = "postgres"
            db_user = "postgres"
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            
            if not db_password:
                logger.error("未找到SUPABASE_DB_PASSWORD环境变量")
                return False
            
            logger.info(f"使用pg8000连接到PostgreSQL数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
            
            # 连接到数据库
            conn = pg8000.connect(
                database=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            
            logger.info("pg8000数据库连接成功")
            
            # 测试连接
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            
            logger.info(f"PostgreSQL版本: {version[0]}")
            
            # 关闭连接
            cursor.close()
            conn.close()
            
            return True
        except ImportError:
            logger.error("pg8000未安装")
            return False
        except Exception as e:
            logger.error(f"pg8000数据库连接失败: {e}")
            logger.error(traceback.format_exc())
            return False

def main():
    """主函数"""
    logger.info("开始测试Supabase编码问题解决方案")
    
    # 测试解决方案1：使用编码转换中间层
    logger.info("\n=== 测试解决方案1：使用编码转换中间层 ===")
    solution1_success = Solution1_EncodingMiddleware.connect_to_supabase_db()
    logger.info(f"解决方案1结果: {'成功' if solution1_success else '失败'}")
    
    # 测试解决方案2：直接使用连接参数
    logger.info("\n=== 测试解决方案2：直接使用连接参数 ===")
    solution2_success = Solution2_DirectParameters.connect_to_supabase_db()
    logger.info(f"解决方案2结果: {'成功' if solution2_success else '失败'}")
    
    # 测试解决方案3：使用REST API
    logger.info("\n=== 测试解决方案3：使用REST API ===")
    solution3_success = Solution3_RestAPI.connect_to_supabase_api()
    logger.info(f"解决方案3结果: {'成功' if solution3_success else '失败'}")
    
    # 测试解决方案4：使用替代PostgreSQL客户端
    logger.info("\n=== 测试解决方案4：使用替代PostgreSQL客户端 ===")
    solution4_success = Solution4_AlternativeClient.connect_with_pg8000()
    logger.info(f"解决方案4结果: {'成功' if solution4_success else '失败'}")
    
    # 总结结果
    logger.info("\n=== 解决方案测试结果摘要 ===")
    logger.info(f"解决方案1（编码转换中间层）: {'成功' if solution1_success else '失败'}")
    logger.info(f"解决方案2（直接使用连接参数）: {'成功' if solution2_success else '失败'}")
    logger.info(f"解决方案3（使用REST API）: {'成功' if solution3_success else '失败'}")
    logger.info(f"解决方案4（使用替代PostgreSQL客户端）: {'成功' if solution4_success else '失败'}")
    
    # 推荐最佳解决方案
    if solution3_success:
        logger.info("推荐解决方案: 使用REST API（解决方案3）")
    elif solution4_success:
        logger.info("推荐解决方案: 使用替代PostgreSQL客户端（解决方案4）")
    elif solution1_success:
        logger.info("推荐解决方案: 使用编码转换中间层（解决方案1）")
    elif solution2_success:
        logger.info("推荐解决方案: 直接使用连接参数（解决方案2）")
    else:
        logger.error("所有解决方案均失败，需要进一步调查")
    
    logger.info("Supabase编码问题解决方案测试完成")

if __name__ == "__main__":
    main()

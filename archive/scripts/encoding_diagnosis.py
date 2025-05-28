"""
Supabase编码问题诊断工具

此脚本用于诊断和解决中文Windows环境下与Supabase连接相关的编码问题。
"""

import os
import sys
import locale
import platform
import traceback
import logging
from dotenv import load_dotenv
import urllib.parse

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/encoding_diagnosis.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("encoding_diagnosis")

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

def diagnose_system_encoding():
    """诊断系统编码环境"""
    logger.info("=== 系统编码诊断 ===")
    
    # 获取系统信息
    system_info = {
        "操作系统": platform.system(),
        "操作系统版本": platform.version(),
        "操作系统发行版": platform.release(),
        "Python版本": platform.python_version(),
        "系统默认编码": locale.getpreferredencoding(),
        "Python默认编码": sys.getdefaultencoding(),
        "文件系统编码": sys.getfilesystemencoding(),
        "标准输出编码": sys.stdout.encoding,
        "标准错误编码": sys.stderr.encoding,
        "区域设置": locale.getlocale(),
    }
    
    # 打印系统信息
    for key, value in system_info.items():
        logger.info(f"{key}: {value}")
    
    # 检查是否是中文Windows环境
    is_chinese_windows = (
        system_info["操作系统"] == "Windows" and 
        (system_info["系统默认编码"] == "cp936" or 
         system_info["区域设置"][0] == "zh_CN")
    )
    
    if is_chinese_windows:
        logger.warning("检测到中文Windows环境，可能会导致编码问题")
    
    return system_info

def test_encoding_conversion():
    """测试编码转换"""
    logger.info("=== 编码转换测试 ===")
    
    # 测试字符串
    test_strings = [
        "Hello, World!",  # 英文
        "你好，世界！",    # 中文
        "こんにちは世界！", # 日文
        "안녕하세요 세계!", # 韩文
        "Привет, мир!",   # 俄文
        "Olá, mundo!",    # 葡萄牙文
        "Hola, mundo!",   # 西班牙文
        "Bonjour, monde!", # 法文
        "Hallo, Welt!",   # 德文
        "Ciao, mondo!",   # 意大利文
        "Γειά σου Κόσμε!", # 希腊文
        "مرحبا بالعالم!",  # 阿拉伯文
        "שלום עולם!",     # 希伯来文
        "नमस्ते दुनिया!",  # 印地文
        "ສະບາຍດີຊາວໂລກ!", # 老挝文
        "สวัสดีชาวโลก!",   # 泰文
        "Xin chào thế giới!", # 越南文
    ]
    
    # 测试不同编码之间的转换
    encodings = ["utf-8", "gbk", "cp936", "iso-8859-1", "shift_jis", "euc-kr"]
    
    for test_string in test_strings:
        logger.info(f"测试字符串: {test_string}")
        
        for src_encoding in encodings:
            try:
                # 尝试编码
                encoded = test_string.encode(src_encoding)
                logger.info(f"  成功编码为 {src_encoding}: {encoded}")
                
                # 尝试解码回不同的编码
                for dst_encoding in encodings:
                    try:
                        decoded = encoded.decode(dst_encoding)
                        if decoded == test_string:
                            logger.info(f"  成功从 {src_encoding} 解码为 {dst_encoding}: 匹配")
                        else:
                            logger.warning(f"  从 {src_encoding} 解码为 {dst_encoding}: 不匹配 - {decoded}")
                    except UnicodeDecodeError as e:
                        logger.error(f"  无法从 {src_encoding} 解码为 {dst_encoding}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"  无法编码为 {src_encoding}: {e}")

def test_url_encoding():
    """测试URL编码"""
    logger.info("=== URL编码测试 ===")
    
    # 测试密码字符串
    test_passwords = [
        "simple_password",
        "Password123!",
        "复杂密码123!@#",
        "パスワード123!@#",
        "비밀번호123!@#",
        "Пароль123!@#",
        "كلمة المرور123!@#",
        "סיסמה123!@#",
    ]
    
    for password in test_passwords:
        logger.info(f"测试密码: {password}")
        
        # URL编码
        url_encoded = urllib.parse.quote(password)
        logger.info(f"  URL编码: {url_encoded}")
        
        # URL解码
        url_decoded = urllib.parse.unquote(url_encoded)
        if url_decoded == password:
            logger.info(f"  URL解码: 匹配")
        else:
            logger.warning(f"  URL解码: 不匹配 - {url_decoded}")
        
        # 双重URL编码
        double_encoded = urllib.parse.quote(url_encoded)
        logger.info(f"  双重URL编码: {double_encoded}")
        
        # 双重URL解码
        double_decoded = urllib.parse.unquote(urllib.parse.unquote(double_encoded))
        if double_decoded == password:
            logger.info(f"  双重URL解码: 匹配")
        else:
            logger.warning(f"  双重URL解码: 不匹配 - {double_decoded}")

def test_env_variables():
    """测试环境变量"""
    logger.info("=== 环境变量测试 ===")
    
    # 加载环境变量
    load_dotenv()
    
    # 检查必要的环境变量
    required_vars = [
        'DATABASE_URL',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_KEY',
        'SUPABASE_JWT_SECRET',
        'SUPABASE_DB_PASSWORD'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 隐藏敏感信息
            if 'KEY' in var or 'PASSWORD' in var or 'SECRET' in var:
                masked_value = value[:5] + '...' + value[-5:] if len(value) > 10 else '***'
                logger.info(f"{var}: {masked_value} (已设置)")
            else:
                logger.info(f"{var}: {value}")
        else:
            logger.warning(f"{var}: 未设置")
    
    # 检查DATABASE_URL格式
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgresql://'):
            logger.info("DATABASE_URL格式正确 (PostgreSQL)")
            
            # 解析URL
            try:
                # 分离用户名密码部分和主机部分
                auth_host_parts = database_url.replace('postgresql://', '').split('@', 1)
                
                if len(auth_host_parts) != 2:
                    logger.error("DATABASE_URL格式错误，缺少@符号")
                else:
                    auth_part = auth_host_parts[0]
                    host_part = auth_host_parts[1]
                    
                    # 分离用户名和密码
                    if ':' in auth_part:
                        user, password = auth_part.split(':', 1)
                        logger.info(f"数据库用户名: {user}")
                        logger.info(f"数据库密码: {'*' * len(password)}")
                        
                        # 检查密码中的特殊字符
                        special_chars = [c for c in password if not c.isalnum()]
                        if special_chars:
                            logger.warning(f"数据库密码包含特殊字符: {special_chars}")
                            
                            # 尝试URL编码密码
                            encoded_password = urllib.parse.quote(password)
                            logger.info(f"URL编码后的密码: {encoded_password}")
                            
                            # 构建新的URL
                            new_url = f"postgresql://{user}:{encoded_password}@{host_part}"
                            logger.info(f"建议的新DATABASE_URL: {new_url}")
                    else:
                        logger.warning("DATABASE_URL格式错误，缺少密码")
                    
                    # 分离主机和数据库名
                    if '/' in host_part:
                        host_port, dbname = host_part.split('/', 1)
                        logger.info(f"数据库名: {dbname}")
                        
                        # 分离主机和端口
                        if ':' in host_port:
                            host, port = host_port.split(':', 1)
                            logger.info(f"数据库主机: {host}")
                            logger.info(f"数据库端口: {port}")
                        else:
                            logger.info(f"数据库主机: {host_port}")
                            logger.info(f"数据库端口: 默认 (5432)")
                    else:
                        logger.warning("DATABASE_URL格式错误，缺少数据库名")
            except Exception as e:
                logger.error(f"解析DATABASE_URL失败: {e}")
        elif database_url.startswith('sqlite:///'):
            logger.info("DATABASE_URL格式正确 (SQLite)")
        else:
            logger.warning(f"未知的DATABASE_URL格式: {database_url}")

def test_psycopg2_connection():
    """测试psycopg2连接"""
    logger.info("=== psycopg2连接测试 ===")
    
    try:
        import psycopg2
        logger.info("psycopg2已安装")
        
        # 获取数据库连接参数
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            logger.error("未找到SUPABASE_DB_PASSWORD环境变量")
            return
        
        logger.info(f"连接到PostgreSQL数据库: {db_host}:{db_port}/{db_name} (用户: {db_user})")
        
        # 尝试不同的编码方式
        encodings = ["utf8", "latin1", "gbk", "cp936"]
        
        for encoding in encodings:
            try:
                logger.info(f"尝试使用 {encoding} 编码连接...")
                
                # 连接到数据库
                conn = psycopg2.connect(
                    dbname=db_name,
                    user=db_user,
                    password=db_password,
                    host=db_host,
                    port=db_port,
                    client_encoding=encoding
                )
                
                logger.info(f"使用 {encoding} 编码连接成功")
                
                # 测试连接
                cur = conn.cursor()
                cur.execute("SELECT version()")
                version = cur.fetchone()
                logger.info(f"PostgreSQL版本: {version[0]}")
                
                # 关闭连接
                cur.close()
                conn.close()
                
                logger.info(f"使用 {encoding} 编码连接测试完成")
                return
            except Exception as e:
                logger.error(f"使用 {encoding} 编码连接失败: {e}")
                logger.error(f"错误类型: {type(e).__name__}")
                logger.error(traceback.format_exc())
    except ImportError:
        logger.error("psycopg2未安装")

def main():
    """主函数"""
    logger.info("开始Supabase编码问题诊断")
    
    # 诊断系统编码
    system_info = diagnose_system_encoding()
    
    # 测试编码转换
    test_encoding_conversion()
    
    # 测试URL编码
    test_url_encoding()
    
    # 测试环境变量
    test_env_variables()
    
    # 测试psycopg2连接
    test_psycopg2_connection()
    
    logger.info("Supabase编码问题诊断完成")

if __name__ == "__main__":
    main()

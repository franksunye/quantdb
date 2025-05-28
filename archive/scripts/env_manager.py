"""
环境变量管理工具

此脚本用于管理和验证QuantDB项目的环境变量，特别是与Supabase相关的配置。
"""

import os
import sys
import re
import logging
import argparse
import json
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/env_manager.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("env_manager")

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

class EnvManager:
    """环境变量管理器"""

    def __init__(self, env_file='.env'):
        """初始化环境变量管理器"""
        self.env_file = env_file
        self.env_vars = {}
        self.load_env_file()

    def load_env_file(self):
        """加载环境变量文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.env_file):
                logger.error(f"环境变量文件不存在: {self.env_file}")
                return False

            # 读取文件内容
            with open(self.env_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析环境变量
            pattern = re.compile(r'^([A-Za-z0-9_]+)=(.*)$', re.MULTILINE)
            matches = pattern.findall(content)

            for key, value in matches:
                # 去除注释
                if '#' in value:
                    value = value.split('#')[0].strip()

                # 去除引号
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                self.env_vars[key] = value

            logger.info(f"已加载环境变量文件: {self.env_file}")
            logger.info(f"环境变量数量: {len(self.env_vars)}")

            return True
        except Exception as e:
            logger.error(f"加载环境变量文件失败: {e}")
            return False

    def validate_env_vars(self, required_vars=None):
        """验证环境变量"""
        if required_vars is None:
            required_vars = [
                'DATABASE_URL',
                'SUPABASE_URL',
                'SUPABASE_KEY',
                'SUPABASE_SERVICE_KEY',
                'SUPABASE_JWT_SECRET',
                'SUPABASE_DB_PASSWORD'
            ]

            # 检查是否存在SUPABASE_ACCESS_TOKEN（可选但推荐）
            if 'SUPABASE_ACCESS_TOKEN' in self.env_vars and self.env_vars['SUPABASE_ACCESS_TOKEN']:
                logger.info("检测到SUPABASE_ACCESS_TOKEN环境变量，可用于Supabase Management API")
            else:
                logger.warning("未检测到SUPABASE_ACCESS_TOKEN环境变量，这将限制Supabase Management API的使用")
                logger.warning("请访问 https://app.supabase.com/account/tokens 创建个人访问令牌")
                logger.warning("然后将其添加到.env文件中: SUPABASE_ACCESS_TOKEN=your_token")

        missing_vars = []
        for var in required_vars:
            if var not in self.env_vars or not self.env_vars[var]:
                missing_vars.append(var)

        if missing_vars:
            logger.error(f"缺少以下环境变量: {', '.join(missing_vars)}")
            return False

        logger.info("所有必要的环境变量都已设置")
        return True

    def validate_database_url(self):
        """验证数据库URL格式"""
        database_url = self.env_vars.get('DATABASE_URL')
        if not database_url:
            logger.error("未找到DATABASE_URL环境变量")
            return False

        # 验证PostgreSQL URL格式
        if database_url.startswith('postgresql://'):
            # 检查基本格式
            pattern = re.compile(r'^postgresql://([^:]+):([^@]+)@([^:/]+)(:[0-9]+)?/(.+)$')
            match = pattern.match(database_url)

            if not match:
                logger.error(f"DATABASE_URL格式错误: {database_url}")
                return False

            user, password, host, port, dbname = match.groups()
            port = port[1:] if port else '5432'  # 去除冒号

            logger.info(f"数据库类型: PostgreSQL")
            logger.info(f"数据库用户: {user}")
            logger.info(f"数据库密码: {'*' * len(password)}")
            logger.info(f"数据库主机: {host}")
            logger.info(f"数据库端口: {port}")
            logger.info(f"数据库名称: {dbname}")

            return True
        # 验证SQLite URL格式
        elif database_url.startswith('sqlite:///'):
            path = database_url[10:]

            logger.info(f"数据库类型: SQLite")
            logger.info(f"数据库路径: {path}")

            return True
        else:
            logger.error(f"不支持的数据库URL格式: {database_url}")
            return False

    def validate_supabase_config(self):
        """验证Supabase配置"""
        # 验证Supabase URL
        supabase_url = self.env_vars.get('SUPABASE_URL')
        if not supabase_url:
            logger.error("未找到SUPABASE_URL环境变量")
            return False

        # 验证URL格式
        pattern = re.compile(r'^https://[a-zA-Z0-9-]+\.supabase\.co$')
        if not pattern.match(supabase_url):
            logger.error(f"SUPABASE_URL格式错误: {supabase_url}")
            return False

        # 验证Supabase密钥
        supabase_key = self.env_vars.get('SUPABASE_KEY')
        if not supabase_key:
            logger.error("未找到SUPABASE_KEY环境变量")
            return False

        # 验证JWT格式
        if not supabase_key.count('.') == 2:
            logger.error(f"SUPABASE_KEY不是有效的JWT格式")
            return False

        # 验证服务角色密钥
        supabase_service_key = self.env_vars.get('SUPABASE_SERVICE_KEY')
        if not supabase_service_key:
            logger.error("未找到SUPABASE_SERVICE_KEY环境变量")
            return False

        # 验证JWT格式
        if not supabase_service_key.count('.') == 2:
            logger.error(f"SUPABASE_SERVICE_KEY不是有效的JWT格式")
            return False

        # 验证JWT密钥
        supabase_jwt_secret = self.env_vars.get('SUPABASE_JWT_SECRET')
        if not supabase_jwt_secret:
            logger.error("未找到SUPABASE_JWT_SECRET环境变量")
            return False

        # 验证Supabase访问令牌（可选）
        supabase_access_token = self.env_vars.get('SUPABASE_ACCESS_TOKEN')
        if supabase_access_token:
            # 验证访问令牌格式（通常以sbp_开头）
            if not supabase_access_token.startswith('sbp_'):
                logger.warning(f"SUPABASE_ACCESS_TOKEN格式可能不正确，通常以'sbp_'开头")
            else:
                logger.info("SUPABASE_ACCESS_TOKEN格式正确")

        logger.info("Supabase配置验证通过")
        return True

    def create_env_template(self, output_file='.env.template'):
        """创建环境变量模板文件"""
        try:
            template = """# Database Configuration
# Choose one of the following DATABASE_URL options:

# Option 1: Local SQLite database (for development)
# DATABASE_URL=sqlite:///./database/stock_data.db

# Option 2: Supabase PostgreSQL database (for production)
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres

# Supabase Configuration
SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_KEY=[YOUR_SUPABASE_ANON_KEY]
SUPABASE_SERVICE_KEY=[YOUR_SUPABASE_SERVICE_ROLE_KEY]
SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]
SUPABASE_DB_PASSWORD=[YOUR_SUPABASE_DB_PASSWORD]
# SUPABASE_ACCESS_TOKEN=[YOUR_SUPABASE_PERSONAL_ACCESS_TOKEN] # 用于Supabase Management API

# API Configuration
API_PREFIX=/api/v1
DEBUG=True
ENVIRONMENT=development

# Security
SECRET_KEY=[YOUR_SECRET_KEY]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quantdb.log
"""

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(template)

            logger.info(f"已创建环境变量模板文件: {output_file}")
            return True
        except Exception as e:
            logger.error(f"创建环境变量模板文件失败: {e}")
            return False

    def create_env_file(self, env_vars, output_file='.env'):
        """创建环境变量文件"""
        try:
            # 构建环境变量文件内容
            content = "# QuantDB Environment Variables\n"
            content += f"# Generated by env_manager.py\n"
            content += f"# Date: {os.environ.get('DATE', '')}\n\n"

            # 数据库配置
            content += "# Database Configuration\n"
            if 'DATABASE_URL' in env_vars:
                content += f"DATABASE_URL={env_vars['DATABASE_URL']}\n\n"

            # Supabase配置
            content += "# Supabase Configuration\n"
            for key in ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY', 'SUPABASE_JWT_SECRET', 'SUPABASE_DB_PASSWORD', 'SUPABASE_ACCESS_TOKEN']:
                if key in env_vars:
                    content += f"{key}={env_vars[key]}\n"
            content += "\n"

            # API配置
            content += "# API Configuration\n"
            for key in ['API_PREFIX', 'DEBUG', 'ENVIRONMENT']:
                if key in env_vars:
                    content += f"{key}={env_vars[key]}\n"
            content += "\n"

            # 安全配置
            content += "# Security\n"
            for key in ['SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_MINUTES']:
                if key in env_vars:
                    content += f"{key}={env_vars[key]}\n"
            content += "\n"

            # 日志配置
            content += "# Logging\n"
            for key in ['LOG_LEVEL', 'LOG_FILE']:
                if key in env_vars:
                    content += f"{key}={env_vars[key]}\n"

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"已创建环境变量文件: {output_file}")
            return True
        except Exception as e:
            logger.error(f"创建环境变量文件失败: {e}")
            return False

    def export_env_vars(self, output_file='.env.json', exclude_sensitive=True):
        """导出环境变量到JSON文件"""
        try:
            # 复制环境变量
            env_vars = self.env_vars.copy()

            # 排除敏感信息
            if exclude_sensitive:
                sensitive_keys = ['PASSWORD', 'KEY', 'SECRET']
                for key in list(env_vars.keys()):
                    if any(s in key for s in sensitive_keys):
                        env_vars[key] = '[REDACTED]'

            # 写入JSON文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(env_vars, f, indent=2)

            logger.info(f"已导出环境变量到JSON文件: {output_file}")
            return True
        except Exception as e:
            logger.error(f"导出环境变量到JSON文件失败: {e}")
            return False

    def print_env_summary(self, exclude_sensitive=True):
        """打印环境变量摘要"""
        logger.info("=== 环境变量摘要 ===")

        # 数据库配置
        logger.info("数据库配置:")
        if 'DATABASE_URL' in self.env_vars:
            db_url = self.env_vars['DATABASE_URL']
            if exclude_sensitive and 'postgresql://' in db_url:
                # 隐藏密码
                parts = db_url.split('@')
                if len(parts) == 2:
                    auth_part = parts[0].split(':')
                    if len(auth_part) == 3:  # postgresql://user:password
                        masked_url = f"{auth_part[0]}:{auth_part[1]}:***@{parts[1]}"
                        logger.info(f"  DATABASE_URL: {masked_url}")
                    else:
                        logger.info(f"  DATABASE_URL: {db_url}")
                else:
                    logger.info(f"  DATABASE_URL: {db_url}")
            else:
                logger.info(f"  DATABASE_URL: {db_url}")

        # Supabase配置
        logger.info("Supabase配置:")
        for key in ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY', 'SUPABASE_JWT_SECRET', 'SUPABASE_DB_PASSWORD', 'SUPABASE_ACCESS_TOKEN']:
            if key in self.env_vars:
                value = self.env_vars[key]
                if exclude_sensitive and ('KEY' in key or 'SECRET' in key or 'PASSWORD' in key or 'TOKEN' in key):
                    value = value[:5] + '...' + value[-5:] if len(value) > 10 else '***'
                logger.info(f"  {key}: {value}")

        # API配置
        logger.info("API配置:")
        for key in ['API_PREFIX', 'DEBUG', 'ENVIRONMENT']:
            if key in self.env_vars:
                logger.info(f"  {key}: {self.env_vars[key]}")

        # 安全配置
        logger.info("安全配置:")
        for key in ['SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_MINUTES']:
            if key in self.env_vars:
                value = self.env_vars[key]
                if exclude_sensitive and 'KEY' in key:
                    value = value[:5] + '...' + value[-5:] if len(value) > 10 else '***'
                logger.info(f"  {key}: {value}")

        # 日志配置
        logger.info("日志配置:")
        for key in ['LOG_LEVEL', 'LOG_FILE']:
            if key in self.env_vars:
                logger.info(f"  {key}: {self.env_vars[key]}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='QuantDB环境变量管理工具')
    parser.add_argument('--env-file', default='.env', help='环境变量文件路径')
    parser.add_argument('--validate', action='store_true', help='验证环境变量')
    parser.add_argument('--create-template', action='store_true', help='创建环境变量模板文件')
    parser.add_argument('--export', action='store_true', help='导出环境变量到JSON文件')
    parser.add_argument('--output', default='.env.json', help='导出文件路径')
    parser.add_argument('--summary', action='store_true', help='打印环境变量摘要')

    args = parser.parse_args()

    # 创建环境变量管理器
    env_manager = EnvManager(args.env_file)

    # 验证环境变量
    if args.validate:
        logger.info("验证环境变量...")
        env_manager.validate_env_vars()
        env_manager.validate_database_url()
        env_manager.validate_supabase_config()

    # 创建环境变量模板文件
    if args.create_template:
        logger.info("创建环境变量模板文件...")
        env_manager.create_env_template()

    # 导出环境变量到JSON文件
    if args.export:
        logger.info(f"导出环境变量到JSON文件: {args.output}")
        env_manager.export_env_vars(args.output)

    # 打印环境变量摘要
    if args.summary:
        env_manager.print_env_summary()

    # 如果没有指定任何操作，打印帮助信息
    if not (args.validate or args.create_template or args.export or args.summary):
        parser.print_help()

if __name__ == "__main__":
    main()

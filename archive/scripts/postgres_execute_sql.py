"""
PostgreSQL 执行 SQL 命令工具

此脚本用于在 PostgreSQL 数据库中执行 SQL 命令，支持：
1. 执行单个 SQL 命令
2. 执行 SQL 文件
3. 交互式 SQL 命令执行
"""

import os
import sys
import logging
import argparse
import traceback
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("postgres_execute_sql")

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从 .env 文件加载环境变量
load_dotenv()

def execute_sql_command(sql, params=None):
    """
    执行 SQL 命令
    
    Args:
        sql: SQL 命令
        params: SQL 参数
    
    Returns:
        执行结果
    """
    try:
        from services.postgres_client import get_postgres_client
        
        # 获取客户端
        client = get_postgres_client()
        
        # 判断 SQL 类型
        sql_lower = sql.lower().strip()
        if sql_lower.startswith(("select", "show", "describe", "explain")):
            # 查询操作
            result = client.execute_query_dict(sql, params)
            return result
        else:
            # 非查询操作
            rows_affected = client.execute_non_query(sql, params)
            return {"rows_affected": rows_affected}
    except Exception as e:
        logger.error(f"执行 SQL 命令失败: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def execute_sql_file(file_path):
    """
    执行 SQL 文件
    
    Args:
        file_path: SQL 文件路径
    
    Returns:
        执行结果
    """
    try:
        # 读取 SQL 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 分割 SQL 命令
        sql_commands = sql.split(';')
        
        # 执行每个 SQL 命令
        results = []
        for command in sql_commands:
            command = command.strip()
            if command:
                logger.info(f"执行 SQL 命令: {command[:100]}...")
                result = execute_sql_command(command)
                results.append(result)
        
        return results
    except Exception as e:
        logger.error(f"执行 SQL 文件失败: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def interactive_mode():
    """
    交互式 SQL 命令执行
    """
    try:
        from services.postgres_client import get_postgres_client
        
        # 获取客户端
        client = get_postgres_client()
        
        # 获取数据库版本
        version = client.execute_query_scalar("SELECT version()")
        logger.info(f"连接到 PostgreSQL: {version}")
        
        # 交互式循环
        print("\n欢迎使用 PostgreSQL 交互式命令行工具")
        print("输入 SQL 命令执行，输入 'exit' 或 'quit' 退出\n")
        
        while True:
            # 获取用户输入
            sql = input("SQL> ")
            
            # 检查退出命令
            if sql.lower() in ('exit', 'quit'):
                print("再见！")
                break
            
            # 执行 SQL 命令
            try:
                if sql.strip():
                    # 判断 SQL 类型
                    sql_lower = sql.lower().strip()
                    if sql_lower.startswith(("select", "show", "describe", "explain")):
                        # 查询操作
                        result = client.execute_query_dict(sql)
                        
                        # 打印结果
                        if result:
                            # 获取列宽度
                            col_widths = {}
                            for row in result:
                                for col, val in row.items():
                                    col_widths[col] = max(
                                        col_widths.get(col, len(str(col))),
                                        len(str(val))
                                    )
                            
                            # 打印表头
                            header = " | ".join(
                                f"{col:{col_widths[col]}}" for col in result[0].keys()
                            )
                            print("\n" + header)
                            print("-" * len(header))
                            
                            # 打印数据
                            for row in result:
                                print(" | ".join(
                                    f"{str(val):{col_widths[col]}}" for col, val in row.items()
                                ))
                            
                            print(f"\n{len(result)} 行结果\n")
                        else:
                            print("查询没有返回结果\n")
                    else:
                        # 非查询操作
                        rows_affected = client.execute_non_query(sql)
                        print(f"命令执行成功，影响了 {rows_affected} 行\n")
            except Exception as e:
                print(f"错误: {e}\n")
    except Exception as e:
        logger.error(f"交互式模式失败: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PostgreSQL 执行 SQL 命令工具")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--command", help="要执行的 SQL 命令")
    group.add_argument("-f", "--file", help="要执行的 SQL 文件路径")
    group.add_argument("-i", "--interactive", action="store_true", help="交互式模式")
    
    args = parser.parse_args()
    
    if args.command:
        # 执行单个 SQL 命令
        logger.info(f"执行 SQL 命令: {args.command}")
        result = execute_sql_command(args.command)
        print(result)
    elif args.file:
        # 执行 SQL 文件
        logger.info(f"执行 SQL 文件: {args.file}")
        result = execute_sql_file(args.file)
        print(result)
    elif args.interactive:
        # 交互式模式
        logger.info("启动交互式模式")
        interactive_mode()
    else:
        # 显示帮助信息
        parser.print_help()

if __name__ == "__main__":
    main()

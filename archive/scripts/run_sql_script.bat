@echo off
REM 执行 SQL 脚本的批处理脚本

if "%1"=="" (
    echo 用法: run_sql_script.bat <sql_script_path>
    exit /b 1
)

set SQL_SCRIPT=%1

echo 正在执行 SQL 脚本: %SQL_SCRIPT%
echo 主机: db.dvusiqfijdmjcsubyapw.supabase.co
echo 端口: 5432
echo 数据库: postgres
echo 用户: postgres

REM 从 .env 文件读取密码
for /f "tokens=2 delims==" %%a in ('findstr /C:"SUPABASE_DB_PASSWORD" .env') do set DB_PASSWORD=%%a

REM 执行 SQL 脚本
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=%DB_PASSWORD% sslmode=require" -f %SQL_SCRIPT%

echo SQL 脚本执行完成。

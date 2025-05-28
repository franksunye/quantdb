@echo off
REM 连接到 Supabase PostgreSQL 数据库的批处理脚本

echo 正在连接到 Supabase PostgreSQL 数据库...
echo 主机: db.dvusiqfijdmjcsubyapw.supabase.co
echo 端口: 5432
echo 数据库: postgres
echo 用户: postgres

REM 从 .env 文件读取密码
for /f "tokens=2 delims==" %%a in ('findstr /C:"SUPABASE_DB_PASSWORD" .env') do set DB_PASSWORD=%%a

REM 连接到数据库
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=%DB_PASSWORD% sslmode=require"

echo 连接已关闭。

# 连接到Supabase PostgreSQL数据库的Pooler
# 使用Session Pooler而不是直接连接，解决IPv4兼容性问题

# 加载.env文件中的环境变量
$envFile = ".env"
$envVars = @{}

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $envVars[$key] = $value
        }
    }
    Write-Host "已加载环境变量"
} else {
    Write-Host "错误: 未找到.env文件"
    exit 1
}

# 获取数据库连接信息
$dbHost = "aws-0-us-west-1.pooler.supabase.com"
$dbPort = 6543
$dbName = "postgres"
$dbUser = "postgres.dvusiqfijdmjcsubyapw"
$dbPassword = $envVars["SUPABASE_DB_PASSWORD"]

# 显示连接信息
Write-Host "连接到Supabase PostgreSQL数据库(使用Session Pooler)..."
Write-Host "主机: $dbHost"
Write-Host "端口: $dbPort"
Write-Host "数据库: $dbName"
Write-Host "用户: $dbUser"

# 构建连接字符串
$connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword"

# 连接到数据库
& psql $connectionString

Write-Host "连接已关闭。"

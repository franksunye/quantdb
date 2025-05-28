# Initialize Supabase database
# 
# Author: QuantDB Team
# Date: 2025-05-19

# Load environment variables from .env file
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
    Write-Host "Environment variables loaded"
} else {
    Write-Host "Error: .env file not found"
    exit 1
}

# Get database connection info
$dbHost = "aws-0-us-west-1.pooler.supabase.com"
$dbPort = 6543  # Transaction Pooler port
$dbName = "postgres"
$dbUser = "postgres.dvusiqfijdmjcsubyapw"
$dbPassword = $envVars["SUPABASE_DB_PASSWORD"]
$sslCert = "prod-ca-2021.crt"

# Display connection info
Write-Host "Initializing Supabase PostgreSQL database..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SSL Certificate: $sslCert"

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

# Create assets table
Write-Host "Creating assets table..."
$createAssetsTable = @"
CREATE TABLE IF NOT EXISTS assets (
    asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    isin TEXT NOT NULL UNIQUE,
    asset_type TEXT NOT NULL,
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"@
echo $createAssetsTable | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Create daily_stock_data table
Write-Host "Creating daily_stock_data table..."
$createDailyStockDataTable = @"
CREATE TABLE IF NOT EXISTS daily_stock_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL,
    trade_date DATE NOT NULL,
    open NUMERIC(10, 2),
    high NUMERIC(10, 2),
    low NUMERIC(10, 2),
    close NUMERIC(10, 2),
    volume BIGINT,
    turnover NUMERIC(20, 2),
    amplitude NUMERIC(10, 4),
    pct_change NUMERIC(10, 4),
    change NUMERIC(10, 4),
    turnover_rate NUMERIC(10, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
    UNIQUE (asset_id, trade_date)
);
"@
echo $createDailyStockDataTable | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Create indexes
Write-Host "Creating indexes..."
$createIndexes = @"
CREATE INDEX IF NOT EXISTS idx_assets_symbol ON assets (symbol);
CREATE INDEX IF NOT EXISTS idx_daily_stock_data_asset_id ON daily_stock_data (asset_id);
CREATE INDEX IF NOT EXISTS idx_daily_stock_data_trade_date ON daily_stock_data (trade_date);
"@
echo $createIndexes | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Verify tables
Write-Host "Verifying tables..."
$verifyTables = @"
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"@
echo $verifyTables | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host "Database initialization completed."

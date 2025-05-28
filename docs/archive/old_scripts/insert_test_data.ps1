# Insert test data into Supabase database
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
Write-Host "Inserting test data into Supabase PostgreSQL database..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SSL Certificate: $sslCert"

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

# Insert test asset
Write-Host "Inserting test asset..."
$insertAsset = @"
INSERT INTO assets (symbol, name, isin, asset_type, exchange, currency)
VALUES ('000001', '平安银行', 'CNE000000040', 'STOCK', 'SZSE', 'CNY')
ON CONFLICT (isin) DO UPDATE SET
    symbol = EXCLUDED.symbol,
    name = EXCLUDED.name,
    asset_type = EXCLUDED.asset_type,
    exchange = EXCLUDED.exchange,
    currency = EXCLUDED.currency,
    updated_at = NOW()
RETURNING asset_id;
"@
$assetResult = echo $insertAsset | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser" -t
Write-Host "Asset result: $assetResult"

# Get asset ID
$assetId = $assetResult.Trim()
if ($assetId -match "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})") {
    $assetId = $matches[1]
    Write-Host "Asset ID: $assetId"
} else {
    Write-Host "Error: Failed to get asset ID"
    exit 1
}

# Insert test stock data
Write-Host "Inserting test stock data..."
$today = Get-Date -Format "yyyy-MM-dd"
$yesterday = (Get-Date).AddDays(-1) | Get-Date -Format "yyyy-MM-dd"

$insertStockData = @"
INSERT INTO daily_stock_data (asset_id, trade_date, open, high, low, close, volume, turnover, amplitude, pct_change, change, turnover_rate)
VALUES
    ('$assetId', '$yesterday', 10.5, 11.2, 10.3, 11.0, 1000000, 10500000, 0.086, 0.048, 0.5, 0.012),
    ('$assetId', '$today', 11.0, 11.5, 10.8, 11.3, 1200000, 13200000, 0.064, 0.027, 0.3, 0.014)
ON CONFLICT (asset_id, trade_date) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    turnover = EXCLUDED.turnover,
    amplitude = EXCLUDED.amplitude,
    pct_change = EXCLUDED.pct_change,
    change = EXCLUDED.change,
    turnover_rate = EXCLUDED.turnover_rate,
    updated_at = NOW()
RETURNING id, trade_date, close;
"@
echo $insertStockData | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Verify data
Write-Host "Verifying data..."
$verifyData = @"
SELECT a.symbol, a.name, d.trade_date, d.open, d.close
FROM assets a
JOIN daily_stock_data d ON a.asset_id = d.asset_id
WHERE a.symbol = '000001'
ORDER BY d.trade_date;
"@
echo $verifyData | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host "Test data insertion completed."

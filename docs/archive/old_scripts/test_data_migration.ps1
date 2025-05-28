# Test data migration to Supabase
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
Write-Host "Testing data migration to Supabase PostgreSQL database..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SSL Certificate: $sslCert"

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

# SQL command to insert test asset (using a two-step approach)
$checkAssetSQL = @"
SELECT asset_id FROM assets WHERE symbol = '000001' LIMIT 1;
"@

# Check if asset already exists
Write-Host "Checking if asset already exists..."
$assetIdResult = echo $checkAssetSQL | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser" -t

# Trim the result
$assetId = $assetIdResult.Trim()

# If asset doesn't exist, insert it
if ([string]::IsNullOrWhiteSpace($assetId)) {
    $insertAssetSQL = @"
    INSERT INTO assets (symbol, name, isin, asset_type, exchange, currency)
    VALUES ('000001', '平安银行', 'CNE000000040', 'STOCK', 'SZSE', 'CNY')
    RETURNING asset_id;
"@

    Write-Host "Inserting test asset..."
    $assetId = echo $insertAssetSQL | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser" -t
    $assetId = $assetId.Trim()
    Write-Host "Asset inserted with ID: $assetId"
} else {
    Write-Host "Asset already exists with ID: $assetId"
}

# SQL command to insert test stock data
$checkStockDataSQL = @"
SELECT id FROM daily_stock_data WHERE asset_id = '$assetId' AND trade_date = '2025-05-19' LIMIT 1;
"@

# Check if stock data already exists
Write-Host "Checking if stock data already exists..."
$stockDataIdResult = echo $checkStockDataSQL | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser" -t

# Trim the result
$stockDataId = $stockDataIdResult.Trim()

# If stock data doesn't exist, insert it
if ([string]::IsNullOrWhiteSpace($stockDataId)) {
    $insertStockDataSQL = @"
    INSERT INTO daily_stock_data (asset_id, trade_date, open, high, low, close, volume, turnover, amplitude, pct_change, change, turnover_rate)
    VALUES ('$assetId', '2025-05-19', 10.5, 11.2, 10.3, 11.0, 1000000, 10500000, 0.086, 0.048, 0.5, 0.012)
    RETURNING id;
"@

    Write-Host "Inserting test stock data..."
    $stockDataId = echo $insertStockDataSQL | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser" -t
    $stockDataId = $stockDataId.Trim()
    Write-Host "Stock data inserted with ID: $stockDataId"
} else {
    Write-Host "Stock data already exists with ID: $stockDataId"
}

# SQL command to verify data
$verifyDataSQL = @"
SELECT a.symbol, a.name, d.trade_date, d.open, d.close
FROM assets a
JOIN daily_stock_data d ON a.asset_id = d.asset_id
WHERE a.symbol = '000001';
"@

# Execute SQL command
Write-Host "Verifying data..."
echo $verifyDataSQL | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host "Data migration test completed."

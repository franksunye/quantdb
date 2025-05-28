# Connect to Supabase PostgreSQL database with SSL certificate PowerShell script

# Read .env file
$envFile = Join-Path $PSScriptRoot "..\.env"
$envContent = Get-Content $envFile

# Parse environment variables
$envVars = @{}
foreach ($line in $envContent) {
    if ($line -match '^\s*([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $envVars[$key] = $value
    }
}

# Get database connection info
$dbHost = "db.dvusiqfijdmjcsubyapw.supabase.co"
$dbPort = 5432
$dbName = "postgres"
$dbUser = "postgres"
$dbPassword = $envVars["SUPABASE_DB_PASSWORD"]
$sslCert = Join-Path $PSScriptRoot "..\prod-ca-2021.crt"

# Check if SSL certificate exists
if (-not (Test-Path $sslCert)) {
    $sslCert = "prod-ca-2021.crt"
    if (-not (Test-Path $sslCert)) {
        Write-Host "Warning: SSL certificate file not found. Using sslmode=require instead of verify-full."
        $sslMode = "require"
        $sslCertParam = ""
    } else {
        $sslMode = "verify-full"
        $sslCertParam = "sslrootcert=$sslCert"
    }
} else {
    $sslMode = "verify-full"
    $sslCertParam = "sslrootcert=$sslCert"
}

# Display connection info
Write-Host "Connecting to Supabase PostgreSQL database with SSL..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SSL Mode: $sslMode"
if ($sslMode -eq "verify-full") {
    Write-Host "SSL Certificate: $sslCert"
}

# Build connection string
if ($sslMode -eq "verify-full") {
    $connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword sslmode=$sslMode $sslCertParam"
} else {
    $connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword sslmode=$sslMode"
}

# Connect to database
& psql $connectionString

Write-Host "Connection closed."

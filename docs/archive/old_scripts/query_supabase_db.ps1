# Query Supabase PostgreSQL database PowerShell script
# Updated to use Transaction Pooler for IPv4 compatibility

param (
    [Parameter(Mandatory=$true)]
    [string]$SqlQuery
)

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
$dbHost = "aws-0-us-west-1.pooler.supabase.com"  # Transaction Pooler host
$dbPort = 6543  # Transaction Pooler port
$dbName = "postgres"
$dbUser = "postgres.dvusiqfijdmjcsubyapw"
$dbPassword = $envVars["SUPABASE_DB_PASSWORD"]
$sslCert = Join-Path $PSScriptRoot "..\prod-ca-2021.crt"

# Display query info
Write-Host "Querying Supabase PostgreSQL database (using Transaction Pooler)..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SSL Certificate: $sslCert"
Write-Host "SQL Query: $SqlQuery"

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

# Execute query using psql with SSL verification
& psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser" -c $SqlQuery

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host "Query execution completed."

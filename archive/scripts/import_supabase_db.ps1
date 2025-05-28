# Import data to Supabase PostgreSQL database PowerShell script

param (
    [Parameter(Mandatory=$true)]
    [string]$SqlFile
)

# Check if file exists
if (-not (Test-Path $SqlFile)) {
    Write-Host "Error: SQL file does not exist: $SqlFile"
    exit 1
}

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

# Display import info
Write-Host "Importing data to Supabase PostgreSQL database..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SQL File: $SqlFile"

# Build connection string
$connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword sslmode=require"

# Import data
& psql $connectionString -f $SqlFile

Write-Host "Data import completed."

# Connect to Supabase PostgreSQL database PowerShell script

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

# Display connection info
Write-Host "Connecting to Supabase PostgreSQL database..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"

# Build connection string
$connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword sslmode=require"

# Connect to database
& psql $connectionString

Write-Host "Connection closed."

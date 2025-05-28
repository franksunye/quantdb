# Execute SQL script PowerShell script

param (
    [Parameter(Mandatory=$true)]
    [string]$SqlScriptPath
)

# Check if file exists
if (-not (Test-Path $SqlScriptPath)) {
    Write-Host "Error: SQL script file does not exist: $SqlScriptPath"
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

# Display connection info
Write-Host "Executing SQL script: $SqlScriptPath"
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"

# Build connection string
$connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword sslmode=require"

# Execute SQL script
& psql $connectionString -f $SqlScriptPath

Write-Host "SQL script execution completed."

# Execute SQL command on Supabase PostgreSQL database
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

# Get SQL command from command line
$sqlCommand = $args[0]
if (-not $sqlCommand) {
    $sqlCommand = "SELECT 1 as test;"
}

# Display connection info
Write-Host "Executing SQL command on Supabase PostgreSQL database..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"
Write-Host "SSL Certificate: $sslCert"
Write-Host "SQL Command: $sqlCommand"

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

# Execute SQL command
Write-Host "Executing SQL command..."
echo $sqlCommand | & psql "sslmode=verify-full sslrootcert=$sslCert host=$dbHost port=$dbPort dbname=$dbName user=$dbUser"

# Check if the command was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "SQL command executed successfully"
} else {
    Write-Host "Error: Failed to execute SQL command (Exit code: $LASTEXITCODE)"
}

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host "Command execution completed."

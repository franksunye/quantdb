# Connect to Supabase PostgreSQL database using Pooler with environment variable
# Use Session Pooler instead of direct connection to solve IPv4 compatibility issues

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
$dbPort = 6543  # Using Transaction Pooler
$dbName = "postgres"
$dbUser = "postgres.dvusiqfijdmjcsubyapw"
$dbPassword = $envVars["SUPABASE_DB_PASSWORD"]

# Display connection info
Write-Host "Connecting to Supabase PostgreSQL database (using Session Pooler)..."
Write-Host "Host: $dbHost"
Write-Host "Port: $dbPort"
Write-Host "Database: $dbName"
Write-Host "User: $dbUser"

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

# Connect to database using psql with environment variable for password
& psql -h $dbHost -p $dbPort -d $dbName -U $dbUser

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host "Connection closed."

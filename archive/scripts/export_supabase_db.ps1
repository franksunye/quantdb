# Export Supabase PostgreSQL database PowerShell script

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

# Create export directory
$exportDir = Join-Path $PSScriptRoot "..\database\export"
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir | Out-Null
}

# Get current timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Export database schema
$schemaFile = Join-Path $exportDir "supabase_schema_$timestamp.sql"
Write-Host "Exporting database schema to: $schemaFile"

# Build connection string
$connectionString = "host=$dbHost port=$dbPort dbname=$dbName user=$dbUser password=$dbPassword sslmode=require"

# Export database schema
& pg_dump $connectionString --schema-only --no-owner --no-acl -f $schemaFile

# Export table data
$tables = @("assets", "prices")
foreach ($table in $tables) {
    $dataFile = Join-Path $exportDir "supabase_${table}_data_$timestamp.sql"
    Write-Host "Exporting $table table data to: $dataFile"

    # Export table data
    & pg_dump $connectionString --data-only --table=public.$table --no-owner --no-acl -f $dataFile
}

# Create full backup
$fullBackupFile = Join-Path $exportDir "supabase_full_backup_$timestamp.sql"
Write-Host "Creating full backup to: $fullBackupFile"

# Export full backup
& pg_dump $connectionString --no-owner --no-acl -f $fullBackupFile

Write-Host "Database export completed."
Write-Host "Export files are located at: $exportDir"

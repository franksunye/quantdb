# Cleanup Supabase Scripts
# This script organizes and cleans up Supabase-related scripts
# Keeping only the necessary ones and moving others to an archive folder
#
# Author: QuantDB Team
# Date: 2025-05-19

# Create archive directory if it doesn't exist
$archiveDir = "scripts\archive\supabase"
if (-not (Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    Write-Host "Created archive directory: $archiveDir"
}

# Scripts to keep (essential scripts)
$scriptsToKeep = @(
    "connect_pooler_env.ps1",
    "connect_supabase_pooler_simple.ps1",
    "test_transaction_pooler.ps1",
    "query_supabase_db.ps1"
)

# Move all other Supabase-related scripts to archive
Get-ChildItem -Path "scripts" -File | Where-Object { 
    $_.Name -like "*supabase*" -and $scriptsToKeep -notcontains $_.Name 
} | ForEach-Object {
    $destPath = Join-Path $archiveDir $_.Name
    Move-Item -Path $_.FullName -Destination $destPath -Force
    Write-Host "Moved to archive: $($_.Name)"
}

Write-Host "Cleanup completed. Essential scripts kept, others moved to archive."

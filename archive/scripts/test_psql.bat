@echo off
REM Test if psql command is available

echo Testing psql command...
psql --version

if %ERRORLEVEL% EQU 0 (
    echo psql command is available.
) else (
    echo psql command is not available. Please make sure PostgreSQL client tools are installed and added to PATH.
)

pause

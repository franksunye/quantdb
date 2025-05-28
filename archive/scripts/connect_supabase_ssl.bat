@echo off
REM Connect to Supabase PostgreSQL database with SSL certificate

echo Connecting to Supabase PostgreSQL database with SSL certificate...
echo Host: db.dvusiqfijdmjcsubyapw.supabase.co
echo Port: 5432
echo Database: postgres
echo User: postgres
echo SSL Mode: verify-full
echo SSL Certificate: prod-ca-2021.crt

REM Read password from .env file
for /f "tokens=2 delims==" %%a in ('findstr /C:"SUPABASE_DB_PASSWORD" .env') do set DB_PASSWORD=%%a

REM Connect to database
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=%DB_PASSWORD% sslmode=verify-full sslrootcert=prod-ca-2021.crt"

echo Connection closed.

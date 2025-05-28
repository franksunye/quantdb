# Using psql Tool to Connect to Supabase PostgreSQL Database

This document provides detailed guidance on using the PostgreSQL client tool `psql` to connect to and operate the Supabase PostgreSQL database.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Connecting to the Database](#connecting-to-the-database)
   - [Direct Connection (IPv6 Only)](#direct-connection-ipv6-only)
   - [Connection Pooler (IPv4 Compatible)](#connection-pooler-ipv4-compatible)
3. [Executing SQL Scripts](#executing-sql-scripts)
4. [Exporting the Database](#exporting-the-database)
5. [Importing the Database](#importing-the-database)
6. [Querying the Database](#querying-the-database)
7. [Common psql Commands](#common-psql-commands)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

1. Install PostgreSQL client tools (including `psql`, `pg_dump`, etc.)
2. Add PostgreSQL client tools to the system PATH
3. Configure Supabase database password in the `.env` file:

```
SUPABASE_DB_PASSWORD=your_password_here
```

4. Download the SSL certificate file `prod-ca-2021.crt` from Supabase and place it in the project root directory

## Connecting to the Database

> **IMPORTANT**: Supabase direct database connections only support IPv6 by default. If you're on an IPv4 network, you must use the Connection Pooler method described below.

### Direct Connection (IPv6 Only)

> **NOTE**: This method only works if you have IPv6 connectivity or have purchased the IPv4 add-on from Supabase.

#### Using Batch Script

```bash
scripts\connect_supabase.bat
```

#### Using PowerShell Script

```powershell
.\scripts\connect_supabase.ps1
```

#### Using SSL Certificate

##### Batch Script

```bash
scripts\connect_supabase_ssl.bat
```

##### PowerShell Script

```powershell
.\scripts\connect_supabase_ssl.ps1
```

#### Manual Connection

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require"
```

#### Manual Connection with SSL Certificate

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt"
```

### Connection Pooler (IPv4 Compatible)

> **RECOMMENDED**: This is the recommended method for connecting from IPv4 networks. Supabase provides two types of connection poolers:
> - **Transaction Pooler**: For stateless applications where each interaction is brief (port 6543)
> - **Session Pooler**: For long-lived connections (port 5432)

#### Using PowerShell with Environment Variable (Transaction Pooler)

```powershell
$env:PGPASSWORD="your_password_here"; psql "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
```

#### Using PowerShell Script (Transaction Pooler)

```powershell
.\scripts\connect_pooler_env.ps1
```

#### Manual Connection String Format (Transaction Pooler)

```bash
psql "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
```

#### Using Session Pooler

```powershell
$env:PGPASSWORD="your_password_here"; psql "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=5432 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
```

## Executing SQL Scripts

### Using Batch Script

```bash
scripts\run_sql_script.bat scripts\init_supabase.sql
```

### Using PowerShell Script

```powershell
.\scripts\run_sql_script.ps1 -SqlScriptPath .\scripts\init_supabase.sql
```

### Using SSL Certificate

```powershell
.\scripts\run_sql_script_ssl.ps1 -SqlScriptPath .\scripts\init_supabase.sql
```

### Manual Execution

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require" -f scripts\init_supabase.sql
```

### Manual Execution with SSL Certificate

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt" -f scripts\init_supabase.sql
```

## Exporting the Database

### Using PowerShell Script

```powershell
.\scripts\export_supabase_db.ps1
```

### Manual Export

Export database schema:

```bash
pg_dump "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require" --schema-only --no-owner --no-acl -f database\export\supabase_schema.sql
```

Export table data:

```bash
pg_dump "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require" --data-only --table=public.assets --no-owner --no-acl -f database\export\supabase_assets_data.sql
```

Create full backup:

```bash
pg_dump "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require" --no-owner --no-acl -f database\export\supabase_full_backup.sql
```

### Manual Export with SSL Certificate

Export database schema with SSL:

```bash
pg_dump "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt" --schema-only --no-owner --no-acl -f database\export\supabase_schema.sql
```

Export table data with SSL:

```bash
pg_dump "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt" --data-only --table=public.assets --no-owner --no-acl -f database\export\supabase_assets_data.sql
```

Create full backup with SSL:

```bash
pg_dump "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt" --no-owner --no-acl -f database\export\supabase_full_backup.sql
```

## Importing the Database

### Using PowerShell Script

```powershell
.\scripts\import_supabase_db.ps1 -SqlFile .\database\export\supabase_full_backup.sql
```

### Manual Import

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require" -f database\export\supabase_full_backup.sql
```

### Manual Import with SSL Certificate

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt" -f database\export\supabase_full_backup.sql
```

## Querying the Database

### Using PowerShell Script

```powershell
.\scripts\query_supabase_db.ps1 -SqlQuery "SELECT * FROM assets LIMIT 10"
```

### Using SSL Certificate

```powershell
.\scripts\query_supabase_ssl.ps1 -SqlQuery "SELECT * FROM assets LIMIT 10"
```

### Manual Query

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require" -c "SELECT * FROM assets LIMIT 10"
```

### Manual Query with SSL Certificate

```bash
psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt" -c "SELECT * FROM assets LIMIT 10"
```

## Common psql Commands

In the `psql` interactive terminal, you can use the following commands:

- `\l` - List all databases
- `\c database_name` - Connect to specified database
- `\dt` - List all tables in the current database
- `\d table_name` - Show table structure
- `\du` - List all users
- `\dn` - List all schemas
- `\df` - List all functions
- `\dv` - List all views
- `\timing` - Toggle query execution time display
- `\e` - Edit query using editor
- `\i file.sql` - Execute SQL file
- `\o file.txt` - Output query results to file
- `\copy` - Import/export data
- `\q` - Exit psql

### SSL-Related Commands

- `SELECT ssl_is_used();` - Check if SSL is being used
- `SELECT ssl_version();` - Show SSL version
- `SELECT ssl_cipher();` - Show SSL cipher

## Troubleshooting

### Connection Issues

1. **IPv4/IPv6 Compatibility Issues**

   If you're getting connection timeouts when trying to connect directly to the database, it's likely because Supabase direct connections only support IPv6 by default:

   ```
   psql: error: connection to server at "db.dvusiqfijdmjcsubyapw.supabase.co" failed: Connection timed out
   ```

   **Solution**: Use the Connection Pooler method instead:

   ```powershell
   $env:PGPASSWORD="your_password_here"; psql "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
   ```

2. **SSL Connection Errors**

   Make sure to use the `sslmode=require` parameter:

   ```bash
   psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=require"
   ```

   For stronger security, use `sslmode=verify-full` with the SSL certificate:

   ```bash
   psql "host=db.dvusiqfijdmjcsubyapw.supabase.co port=5432 dbname=postgres user=postgres password=your_password_here sslmode=verify-full sslrootcert=prod-ca-2021.crt"
   ```

3. **SSL Certificate Issues**

   If you encounter SSL certificate verification errors, make sure:

   - The certificate file `prod-ca-2021.crt` exists in the specified path
   - The certificate file is valid and not corrupted
   - You're using the correct certificate for the Supabase instance

4. **Password Errors**

   If you get "Wrong password" errors:

   ```
   psql: error: connection to server failed: error received from server in SCRAM exchange: Wrong password
   ```

   Check if the `SUPABASE_DB_PASSWORD` in the `.env` file is correct. You may need to reset your database password in the Supabase Dashboard under Database Settings.

5. **Network Issues**

   Ensure your network connection is working properly. You can try pinging the database host:

   ```bash
   ping aws-0-us-west-1.pooler.supabase.com
   ```

6. **Firewall Issues**

   Make sure your firewall allows outbound connections on ports 5432 and 6543.

### Operation Limitations

1. **Write Operations Limitations**

   You may encounter issues when trying to perform write operations (CREATE TABLE, INSERT, etc.) using the Connection Pooler. This is a limitation of the Supabase Connection Pooler.

   **Solution**: For database management operations, consider using:

   - Supabase Dashboard for table creation and management
   - Supabase REST API for data operations
   - SQL scripts executed through the Supabase Dashboard SQL Editor

2. **Chinese Character Issues**

   When inserting Chinese characters, you might encounter connection resets:

   ```
   SSL connection has been closed unexpectedly
   ```

   **Solution**: Use English characters or use the REST API for operations involving non-ASCII characters.

### Encoding Issues

If you encounter Chinese character encoding issues, try the following:

1. Set client encoding:

   ```bash
   psql "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw" -c "SET client_encoding TO 'UTF8';"
   ```

2. In Windows, try changing the console code page:

   ```bash
   chcp 65001
   ```

3. Use PowerShell instead of CMD, as PowerShell has better UTF-8 support.

4. Use the Python script with psycopg2:

   ```bash
   python scripts/test_psycopg2_ssl.py
   ```

### Permission Issues

If you encounter permission issues, it might be because Supabase has certain restrictions on database operations. Make sure you're using the correct user and permissions.

### Other Issues

If you encounter other issues, try using the `-v` parameter to enable verbose output:

```bash
psql -v "sslmode=verify-full sslrootcert=prod-ca-2021.crt host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
```

Or use the `PGSSLMODE` environment variable:

```bash
$env:PGSSLMODE="verify-full"
$env:PGSSLROOTCERT="prod-ca-2021.crt"
$env:PGPASSWORD="your_password_here"
psql "host=aws-0-us-west-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.dvusiqfijdmjcsubyapw"
```

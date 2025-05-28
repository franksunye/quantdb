-- Test connection to Supabase PostgreSQL database

-- Display connection information
SELECT current_database() AS database,
       current_user AS user,
       version() AS version;

-- Check SSL connection
SELECT ssl_is_used() AS ssl_used,
       ssl_version() AS ssl_version,
       ssl_cipher() AS ssl_cipher;

-- List schemas
SELECT schema_name
FROM information_schema.schemata
ORDER BY schema_name;

-- List tables in public schema
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Exit
\q

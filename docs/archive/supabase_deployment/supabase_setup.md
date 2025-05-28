# Supabase Setup Guide

This document provides instructions for setting up Supabase for the QuantDB project.

## 文档信息
**文档类型**: 部署指南
**文档编号**: quantdb-DEPLOY-001
**版本**: 1.2.0
**创建日期**: 2025-05-15
**最后更新**: 2025-05-17
**状态**: 已发布
**负责人**: frank

## Prerequisites

- Supabase account (https://supabase.com)
- Access to the Supabase dashboard
- Python 3.8+ with requests library installed

## Setup Steps

### 1. Create a New Supabase Project

1. Log in to the [Supabase dashboard](https://app.supabase.com)
2. Click "New Project"
3. Enter project details:
   - **Name**: QuantDB
   - **Database Password**: Create a strong password
   - **Region**: Choose a region close to your users
   - **Pricing Plan**: Free tier for development, paid tier for production
4. Click "Create New Project"

**Note**: If your project is in an inactive state, you'll need to resume or restart it from the dashboard before proceeding.

### 2. Get Project Credentials

Once your project is created, you'll need the following credentials:

1. Go to the project dashboard
2. Click on "Settings" in the sidebar
3. Click on "API" in the settings menu
4. Note the following values:
   - **Project URL**: `https://[YOUR_PROJECT_ID].supabase.co`
   - **API Key**: The `anon` public key for client-side requests
   - **Service Role Key**: The `service_role` key for server-side requests (keep this secret)

### 3. Set Up Database Schema

You can set up the database schema in two ways:

#### Option 1: Using the SQL Editor

1. Go to the "SQL Editor" in the Supabase dashboard
2. Create a new query
3. Copy the contents of `database/supabase_schema.sql` from the QuantDB repository
4. Run the query to create the tables

#### Option 2: Using the Setup Script

For a more automated approach, you can use the provided setup script:

1. Update your `.env` file with the Supabase connection details:
   ```
   SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
   SUPABASE_KEY=[YOUR_SUPABASE_ANON_KEY]
   SUPABASE_SERVICE_KEY=[YOUR_SUPABASE_SERVICE_ROLE_KEY]
   ```
2. Run the setup script:
   ```bash
   python scripts/setup_supabase.py
   ```

#### Option 3: Using Database Migrations

For a more controlled approach, you can use database migrations with Alembic:

1. Update your `.env` file with the Supabase connection details:
   ```
   DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres
   ```
2. Run the migration script:
   ```bash
   # This will be implemented in a future sprint
   ```

### 4. Configure Row Level Security (RLS)

For secure multi-user access, configure Row Level Security policies:

1. Go to the "Authentication" section in the Supabase dashboard
2. Enable email authentication
3. Go to the "Table Editor" and select a table
4. Click on "Policies" and create appropriate RLS policies

Example RLS policy for the `assets` table:

```sql
CREATE POLICY "Public assets are viewable by everyone"
ON assets
FOR SELECT
USING (true);
```

### 5. Set Up API Access

1. Update your `.env` file with the Supabase credentials:
   ```
   SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
   SUPABASE_KEY=[YOUR_SUPABASE_API_KEY]
   SUPABASE_SERVICE_KEY=[YOUR_SUPABASE_SERVICE_ROLE_KEY]
   SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]
   ```

2. Test the connection:
   ```bash
   python scripts/run_supabase_tests.py --module test_supabase_connection
   ```

### 6. Run Tests

To verify that your Supabase setup is working correctly, run the provided tests:

```bash
# Run all tests
python scripts/run_supabase_tests.py

# Run specific test modules
python scripts/run_supabase_tests.py --module test_supabase_api
python scripts/run_supabase_tests.py --module test_data_migration

# List available test modules
python scripts/run_supabase_tests.py --list
```

## Database Migration from SQLite to PostgreSQL

When migrating from the local SQLite database to Supabase PostgreSQL:

1. Run the data migration test, which will export data from SQLite and import it to PostgreSQL:
   ```bash
   python scripts/run_supabase_tests.py --module test_data_migration
   ```

2. Alternatively, you can use the data migration script directly:
   ```bash
   python tests/deployment/test_data_migration.py
   ```

3. For production migration, update your `.env` file to use the Supabase database:
   ```
   # Comment out the SQLite database URL
   # DATABASE_URL=sqlite:///./database/stock_data.db

   # Uncomment the PostgreSQL database URL
   DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres
   ```

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Check that your database password is correct
2. Ensure your IP address is allowed in the Supabase dashboard
3. Verify that the database URL is correctly formatted
4. Check if your project is active (not paused or inactive)
5. Verify that your API keys are correct and have not expired

### Schema Issues

If you encounter schema issues:

1. Check for differences between SQLite and PostgreSQL syntax
2. Ensure that all tables have been created correctly
3. Verify that foreign key constraints are properly defined
4. Check for case sensitivity issues (PostgreSQL is case-sensitive)

### RLS Policy Issues

If you encounter issues with Row Level Security policies:

1. Verify that RLS is enabled for your tables
2. Check that your policies are correctly defined
3. Test with both anonymous and authenticated users
4. Use the service role key for administrative operations

## Security Best Practices

1. **Never expose your service role key** in client-side code
2. Always use the anon key for client-side requests
3. Implement proper authentication with JWT validation
4. Use RLS policies to restrict data access based on user roles
5. Regularly rotate your API keys and passwords
6. Monitor database access logs for suspicious activity

## Next Steps

After setting up Supabase:

1. Configure authentication if needed
2. Set up storage buckets for file storage
3. Configure real-time subscriptions if required
4. Set up edge functions for serverless computing
5. Implement a backup strategy for your data
6. Set up monitoring and alerting for your database

## References

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase API Reference](https://supabase.com/docs/reference/javascript/supabase-client)

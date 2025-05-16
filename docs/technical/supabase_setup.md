# Supabase Setup Guide

This document provides instructions for setting up Supabase for the QuantDB project.

## Prerequisites

- Supabase account (https://supabase.com)
- Access to the Supabase dashboard

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
3. Copy the contents of `database/schema.sql` from the QuantDB repository
4. Run the query to create the tables

#### Option 2: Using Database Migrations

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
   SUPABASE_JWT_SECRET=[YOUR_SUPABASE_JWT_SECRET]
   ```

2. Test the connection:
   ```bash
   # This will be implemented in a future sprint
   ```

## Database Migration from SQLite to PostgreSQL

When migrating from the local SQLite database to Supabase PostgreSQL:

1. Export data from SQLite:
   ```bash
   # This will be implemented in a future sprint
   ```

2. Import data to PostgreSQL:
   ```bash
   # This will be implemented in a future sprint
   ```

## Troubleshooting

### Connection Issues

If you encounter connection issues:

1. Check that your database password is correct
2. Ensure your IP address is allowed in the Supabase dashboard
3. Verify that the database URL is correctly formatted

### Schema Issues

If you encounter schema issues:

1. Check for differences between SQLite and PostgreSQL syntax
2. Ensure that all tables have been created correctly
3. Verify that foreign key constraints are properly defined

## Next Steps

After setting up Supabase:

1. Configure authentication if needed
2. Set up storage buckets for file storage
3. Configure real-time subscriptions if required
4. Set up edge functions for serverless computing

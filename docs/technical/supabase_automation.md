# Supabase Automation Tools

This document provides information about the Supabase automation tools available in the QuantDB project. These tools allow you to programmatically manage Supabase projects, databases, API keys, and other resources.

## Overview

The Supabase automation tools consist of several Python scripts that interact with the Supabase Management API to perform various operations. These tools are designed to help automate common tasks such as:

- Creating and managing projects
- Resetting database passwords
- Managing API keys
- Setting up project schemas
- Updating environment variables

## Prerequisites

Before using these tools, you need to:

1. Create a personal access token (PAT) from the [Supabase dashboard](https://app.supabase.com/account/tokens)
   - Log in to the Supabase dashboard
   - Click on your profile icon in the top right corner
   - Select "Account"
   - Go to "Access Tokens" in the left menu
   - Click "Generate New Token"
   - Give it a name (e.g., "QuantDB Management")
   - Select appropriate permissions (usually all are needed)
   - Click "Generate"
   - Copy the generated token (this is the only time you'll see the full token)

2. Set the token as an environment variable:

```bash
# Windows
set SUPABASE_ACCESS_TOKEN=your_access_token

# Linux/macOS
export SUPABASE_ACCESS_TOKEN=your_access_token
```

Alternatively, you can add it to your `.env` file:

```
SUPABASE_ACCESS_TOKEN=your_access_token
```

> **Important Note**: The Supabase Management API requires a personal access token (PAT), not the project's API key or service role key. The PAT is associated with your Supabase account, not with a specific project. For more details, see [Supabase Management API Guide](supabase_management_api.md).

## Available Tools

### 1. Supabase CLI

The main command-line interface that provides access to all functionality.

```bash
python -m scripts.supabase_cli [command] [subcommand] [options]
```

#### Commands:

- `project` - Project management commands
- `db` - Database management commands
- `api-keys` - API keys management commands
- `setup` - Setup and initialization commands
- `env` - Environment management commands

### 2. Project Manager

Manage Supabase projects.

```bash
python -m scripts.supabase_project [command] [options]
```

#### Commands:

- `list` - List all projects
- `get` - Get project details
- `create` - Create a new project
- `pause` - Pause a project
- `resume` - Resume a paused project
- `setup` - Set up a project with schema and initial data

### 3. Database Password Manager

Manage Supabase database passwords.

```bash
python -m scripts.supabase_db_password [command] [options]
```

#### Commands:

- `reset` - Reset the database password
- `update-env` - Update environment variables with the new password

### 4. API Keys Manager

Manage Supabase API keys.

```bash
python -m scripts.supabase_api_keys [command] [options]
```

#### Commands:

- `list` - List all API keys for a project
- `update-env` - Update environment variables with API keys

## Usage Examples

### List All Projects

```bash
python -m scripts.supabase_cli project list
```

### Get Project Details

```bash
python -m scripts.supabase_cli project get your_project_ref
```

### Create a New Project

```bash
python -m scripts.supabase_cli project create "My Project" your_org_id your_db_password --region us-west-1 --wait
```

### Reset Database Password

```bash
python -m scripts.supabase_cli db reset-password your_project_ref --update-env
```

### Execute SQL Query

```bash
python -m scripts.supabase_cli db sql your_project_ref "SELECT NOW();"
```

### List API Keys

```bash
python -m scripts.supabase_cli api-keys list your_project_ref
```

### Update Environment Variables with API Keys

```bash
python -m scripts.supabase_cli api-keys update-env your_project_ref
```

### Perform Full Project Setup

```bash
python -m scripts.supabase_cli setup full your_project_ref database/supabase_schema.sql
```

### Update All Environment Variables

```bash
python -m scripts.supabase_cli env update-all your_project_ref
```

## Common Workflows

### 1. Create a New Project and Set It Up

```bash
# Create a new project
python -m scripts.supabase_cli project create "QuantDB" your_org_id your_db_password --wait

# Set up the project with schema
python -m scripts.supabase_cli setup full your_project_ref database/supabase_schema.sql

# Update all environment variables
python -m scripts.supabase_cli env update-all your_project_ref
```

### 2. Reset Database Password

```bash
# Reset the password and update environment variables
python -m scripts.supabase_cli db reset-password your_project_ref --update-env
```

### 3. Pause and Resume a Project

```bash
# Pause the project
python -m scripts.supabase_cli project pause your_project_ref

# Resume the project
python -m scripts.supabase_cli project resume your_project_ref --wait
```

## Troubleshooting

### API Rate Limits

The Supabase Management API has rate limits. If you encounter rate limit errors, wait a few minutes before trying again.

### Authentication Issues

If you encounter authentication issues:

1. **Invalid Signature Error**: If you see an "invalid signature" error, you are likely using the project's API key or service role key instead of a personal access token. Make sure you're using a PAT generated from your account page.

2. **Token Expiration**: Make sure your personal access token is valid and has not expired. You can create a new token from the Supabase dashboard.

3. **Permission Issues**: Ensure your token has the necessary permissions for the operations you're trying to perform.

### Project Status

Some operations require the project to be in an active state. Use the `--wait` flag with commands like `create` and `resume` to wait for the project to become active.

### Testing Your Setup

You can test your Supabase Management API setup using the provided test script:

```bash
python -m scripts.test_supabase_management_api
```

This script will check if your personal access token is configured correctly and if you can successfully connect to the Management API.

## Additional Resources

- [Supabase Management API Documentation](https://supabase.com/docs/reference/api/introduction)
- [Supabase CLI Documentation](https://supabase.com/docs/reference/cli/introduction)
- [Supabase Dashboard](https://app.supabase.com)

## Contributing

If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

These tools are part of the QuantDB project and are subject to the same license terms.

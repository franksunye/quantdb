#!/usr/bin/env python
"""
Supabase CLI - A comprehensive command-line interface for Supabase

This script provides a unified interface for managing Supabase projects,
databases, API keys, and other resources programmatically.

Usage:
    python -m scripts.supabase_cli [command] [subcommand] [options]

Commands:
    project     - Project management commands
    db          - Database management commands
    api-keys    - API keys management commands
    setup       - Setup and initialization commands
    env         - Environment management commands
"""

import os
import sys
import json
import logging
import argparse
import requests
import time
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv, set_key

# Import specific managers
from scripts.supabase_manager import SupabaseManager
from scripts.supabase_db_password import SupabaseDatabasePasswordManager
from scripts.supabase_api_keys import SupabaseApiKeysManager
from scripts.supabase_project import SupabaseProjectManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("supabase-cli")

class SupabaseCLI:
    """Supabase CLI - Unified interface for Supabase management"""

    def __init__(self, access_token: str = None):
        """
        Initialize the Supabase CLI

        Args:
            access_token: Supabase Management API access token
                          If None, will try to load from SUPABASE_ACCESS_TOKEN env var
                          or fall back to SUPABASE_SERVICE_KEY
        """
        # Load environment variables
        load_dotenv()

        # Set access token - try SUPABASE_ACCESS_TOKEN first, then fall back to SUPABASE_SERVICE_KEY
        self.access_token = access_token or os.getenv('SUPABASE_ACCESS_TOKEN') or os.getenv('SUPABASE_SERVICE_KEY')

        if not self.access_token:
            raise ValueError("Supabase access token not provided. Set SUPABASE_ACCESS_TOKEN or SUPABASE_SERVICE_KEY environment variable or pass as parameter.")

        # Initialize managers
        self.manager = SupabaseManager(self.access_token)
        self.db_password_manager = SupabaseDatabasePasswordManager(self.access_token)
        self.api_keys_manager = SupabaseApiKeysManager(self.access_token)
        self.project_manager = SupabaseProjectManager(self.access_token)

        logger.info("Supabase CLI initialized")

    def setup_project_full(self, project_ref: str, schema_file: str, env_file: str = ".env") -> bool:
        """
        Perform a full project setup

        Args:
            project_ref: Project reference ID
            schema_file: Path to SQL schema file
            env_file: Path to environment file (default: .env)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Performing full setup for project {project_ref}")

            # Wait for project to be active
            if not self.project_manager.wait_for_project_active(project_ref):
                logger.error("Project did not become active in time")
                return False

            # Set up schema
            if not self.project_manager.setup_project(project_ref, schema_file):
                logger.error("Failed to set up project schema")
                return False

            # Update environment variables with API keys
            if not self.api_keys_manager.update_environment_variables(project_ref, env_file):
                logger.error("Failed to update environment variables with API keys")
                return False

            logger.info(f"Project {project_ref} fully set up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to perform full project setup: {str(e)}")
            return False

    def update_all_env_vars(self, project_ref: str, env_file: str = ".env") -> bool:
        """
        Update all environment variables for a project

        Args:
            project_ref: Project reference ID
            env_file: Path to environment file (default: .env)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating all environment variables for project {project_ref}")

            # Get project details
            project = self.project_manager.get_project(project_ref)

            # Get API keys
            api_keys = self.api_keys_manager.get_api_keys(project_ref, reveal=True)

            # Update SUPABASE_URL
            supabase_url = f"https://{project_ref}.supabase.co"
            set_key(env_file, "SUPABASE_URL", supabase_url)

            # Update API keys
            for key in api_keys:
                if key["type"] == "anon":
                    set_key(env_file, "SUPABASE_KEY", key["api_key"])
                elif key["type"] == "service_role":
                    set_key(env_file, "SUPABASE_SERVICE_KEY", key["api_key"])

            # Update DATABASE_URL
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if db_password:
                db_url = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
                set_key(env_file, "DATABASE_URL", db_url)

            logger.info(f"All environment variables updated successfully in {env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to update all environment variables: {str(e)}")
            return False

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Supabase CLI - A comprehensive command-line interface for Supabase")

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Project commands
    project_parser = subparsers.add_parser("project", help="Project management commands")
    project_subparsers = project_parser.add_subparsers(dest="subcommand", help="Project subcommand")

    # List projects
    project_subparsers.add_parser("list", help="List all projects")

    # Get project
    get_project_parser = project_subparsers.add_parser("get", help="Get project details")
    get_project_parser.add_argument("project_ref", help="Project reference ID")

    # Create project
    create_project_parser = project_subparsers.add_parser("create", help="Create a new project")
    create_project_parser.add_argument("name", help="Project name")
    create_project_parser.add_argument("org_id", help="Organization ID")
    create_project_parser.add_argument("db_pass", help="Database password")
    create_project_parser.add_argument("--region", default="us-west-1", help="Region (default: us-west-1)")
    create_project_parser.add_argument("--wait", action="store_true", help="Wait for the project to become active")

    # Pause project
    pause_project_parser = project_subparsers.add_parser("pause", help="Pause a project")
    pause_project_parser.add_argument("project_ref", help="Project reference ID")

    # Resume project
    resume_project_parser = project_subparsers.add_parser("resume", help="Resume a paused project")
    resume_project_parser.add_argument("project_ref", help="Project reference ID")
    resume_project_parser.add_argument("--wait", action="store_true", help="Wait for the project to become active")

    # Database commands
    db_parser = subparsers.add_parser("db", help="Database management commands")
    db_subparsers = db_parser.add_subparsers(dest="subcommand", help="Database subcommand")

    # Reset password
    reset_password_parser = db_subparsers.add_parser("reset-password", help="Reset the database password")
    reset_password_parser.add_argument("project_ref", help="Project reference ID")
    reset_password_parser.add_argument("--password", help="New password (if not provided, a strong password will be generated)")
    reset_password_parser.add_argument("--update-env", action="store_true", help="Update environment variables with the new password")
    reset_password_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Execute SQL
    sql_parser = db_subparsers.add_parser("sql", help="Execute SQL query")
    sql_parser.add_argument("project_ref", help="Project reference ID")
    sql_parser.add_argument("query", help="SQL query to execute")

    # API keys commands
    api_keys_parser = subparsers.add_parser("api-keys", help="API keys management commands")
    api_keys_subparsers = api_keys_parser.add_subparsers(dest="subcommand", help="API keys subcommand")

    # List API keys
    list_keys_parser = api_keys_subparsers.add_parser("list", help="List all API keys for a project")
    list_keys_parser.add_argument("project_ref", help="Project reference ID")
    list_keys_parser.add_argument("--reveal", action="store_true", help="Reveal full API keys")

    # Update environment variables with API keys
    update_env_keys_parser = api_keys_subparsers.add_parser("update-env", help="Update environment variables with API keys")
    update_env_keys_parser.add_argument("project_ref", help="Project reference ID")
    update_env_keys_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Setup commands
    setup_parser = subparsers.add_parser("setup", help="Setup and initialization commands")
    setup_subparsers = setup_parser.add_subparsers(dest="subcommand", help="Setup subcommand")

    # Full setup
    full_setup_parser = setup_subparsers.add_parser("full", help="Perform a full project setup")
    full_setup_parser.add_argument("project_ref", help="Project reference ID")
    full_setup_parser.add_argument("schema_file", help="Path to SQL schema file")
    full_setup_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Environment commands
    env_parser = subparsers.add_parser("env", help="Environment management commands")
    env_subparsers = env_parser.add_subparsers(dest="subcommand", help="Environment subcommand")

    # Update all environment variables
    update_all_env_parser = env_subparsers.add_parser("update-all", help="Update all environment variables for a project")
    update_all_env_parser.add_argument("project_ref", help="Project reference ID")
    update_all_env_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Parse arguments
    args = parser.parse_args()

    # Initialize Supabase CLI
    try:
        cli = SupabaseCLI()

        # Handle commands
        if args.command == "project":
            if args.subcommand == "list":
                projects = cli.project_manager.list_projects()
                print(json.dumps(projects, indent=2))

            elif args.subcommand == "get":
                project = cli.project_manager.get_project(args.project_ref)
                print(json.dumps(project, indent=2))

            elif args.subcommand == "create":
                project = cli.project_manager.create_project(args.name, args.org_id, args.db_pass, args.region)
                print(json.dumps(project, indent=2))

                if args.wait:
                    cli.project_manager.wait_for_project_active(project["id"])

            elif args.subcommand == "pause":
                result = cli.project_manager.pause_project(args.project_ref)
                print(json.dumps(result, indent=2))

            elif args.subcommand == "resume":
                result = cli.project_manager.resume_project(args.project_ref)
                print(json.dumps(result, indent=2))

                if args.wait:
                    cli.project_manager.wait_for_project_active(args.project_ref)

        elif args.command == "db":
            if args.subcommand == "reset-password":
                result = cli.db_password_manager.reset_database_password(args.project_ref, args.password)
                print(f"Database password reset successfully for project {args.project_ref}")
                print(f"New password: {result['new_password']}")

                if args.update_env:
                    success = cli.db_password_manager.update_environment_variables(
                        args.project_ref,
                        result["new_password"],
                        args.env_file
                    )
                    if success:
                        print(f"Environment variables updated successfully in {args.env_file}")
                    else:
                        print(f"Failed to update environment variables in {args.env_file}")

            elif args.subcommand == "sql":
                result = cli.project_manager.execute_sql(args.project_ref, args.query)
                print(json.dumps(result, indent=2))

        elif args.command == "api-keys":
            if args.subcommand == "list":
                api_keys = cli.api_keys_manager.get_api_keys(args.project_ref, args.reveal)
                print(json.dumps(api_keys, indent=2))

            elif args.subcommand == "update-env":
                success = cli.api_keys_manager.update_environment_variables(args.project_ref, args.env_file)
                if success:
                    print(f"Environment variables updated successfully in {args.env_file}")
                else:
                    print(f"Failed to update environment variables in {args.env_file}")

        elif args.command == "setup":
            if args.subcommand == "full":
                success = cli.setup_project_full(args.project_ref, args.schema_file, args.env_file)
                if success:
                    print(f"Project {args.project_ref} fully set up successfully")
                else:
                    print(f"Failed to fully set up project {args.project_ref}")
                    sys.exit(1)

        elif args.command == "env":
            if args.subcommand == "update-all":
                success = cli.update_all_env_vars(args.project_ref, args.env_file)
                if success:
                    print(f"All environment variables updated successfully in {args.env_file}")
                else:
                    print(f"Failed to update all environment variables in {args.env_file}")
                    sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

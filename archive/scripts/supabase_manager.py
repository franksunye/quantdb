#!/usr/bin/env python
"""
Supabase Manager - A utility for automating Supabase operations

This script provides a comprehensive set of tools for managing Supabase projects
programmatically, including project management, database operations, authentication,
and schema management.

Usage:
    python -m scripts.supabase_manager [command] [options]

Commands:
    project     - Project management commands
    db          - Database management commands
    auth        - Authentication management commands
    schema      - Schema management commands
    env         - Environment management commands
"""

import os
import sys
import json
import logging
import argparse
import requests
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("supabase-manager")

class SupabaseManager:
    """Supabase Management API client for automating operations"""

    def __init__(self, access_token: str = None):
        """
        Initialize the Supabase Manager

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

        # Set API base URL
        self.api_base_url = "https://api.supabase.com"

        # Set request headers
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        logger.info("Supabase Manager initialized")

    def _handle_response(self, response: requests.Response, operation: str) -> Any:
        """
        Handle API response

        Args:
            response: Response object
            operation: Operation name

        Returns:
            Processed response data

        Raises:
            Exception: If response status code is not successful
        """
        if response.status_code in (200, 201, 204):
            if response.status_code == 204 or not response.text:
                return None
            return response.json()
        else:
            error_message = f"{operation} failed: {response.status_code} - {response.text}"
            logger.error(error_message)
            raise Exception(error_message)

    # Project Management

    def list_projects(self) -> List[Dict]:
        """
        List all projects

        Returns:
            List of projects
        """
        logger.info("Listing all projects")
        response = requests.get(
            f"{self.api_base_url}/v1/projects",
            headers=self.headers
        )
        return self._handle_response(response, "List projects")

    def get_project(self, project_ref: str) -> Dict:
        """
        Get project details

        Args:
            project_ref: Project reference ID

        Returns:
            Project details
        """
        logger.info(f"Getting project details for {project_ref}")
        response = requests.get(
            f"{self.api_base_url}/v1/projects/{project_ref}",
            headers=self.headers
        )
        return self._handle_response(response, "Get project")

    def create_project(self, name: str, org_id: str, db_pass: str, region: str = "us-west-1") -> Dict:
        """
        Create a new project

        Args:
            name: Project name
            org_id: Organization ID
            db_pass: Database password
            region: Region (default: us-west-1)

        Returns:
            Created project details
        """
        logger.info(f"Creating project {name} in region {region}")
        data = {
            "name": name,
            "organization_id": org_id,
            "db_pass": db_pass,
            "region": region
        }
        response = requests.post(
            f"{self.api_base_url}/v1/projects",
            headers=self.headers,
            json=data
        )
        return self._handle_response(response, "Create project")

    def delete_project(self, project_ref: str) -> Dict:
        """
        Delete a project

        Args:
            project_ref: Project reference ID

        Returns:
            Deletion result
        """
        logger.info(f"Deleting project {project_ref}")
        response = requests.delete(
            f"{self.api_base_url}/v1/projects/{project_ref}",
            headers=self.headers
        )
        return self._handle_response(response, "Delete project")

    def pause_project(self, project_ref: str) -> Dict:
        """
        Pause a project

        Args:
            project_ref: Project reference ID

        Returns:
            Pause result
        """
        logger.info(f"Pausing project {project_ref}")
        response = requests.post(
            f"{self.api_base_url}/v1/projects/{project_ref}/pause",
            headers=self.headers
        )
        return self._handle_response(response, "Pause project")

    # Database Management

    def execute_sql(self, project_ref: str, query: str) -> Dict:
        """
        Execute SQL query

        Args:
            project_ref: Project reference ID
            query: SQL query to execute

        Returns:
            Query result
        """
        logger.info(f"Executing SQL query on project {project_ref}")
        logger.debug(f"SQL query: {query}")
        data = {"query": query}
        response = requests.post(
            f"{self.api_base_url}/v1/projects/{project_ref}/database/query",
            headers=self.headers,
            json=data
        )
        return self._handle_response(response, "Execute SQL")

    def get_postgres_config(self, project_ref: str) -> Dict:
        """
        Get Postgres configuration

        Args:
            project_ref: Project reference ID

        Returns:
            Postgres configuration
        """
        logger.info(f"Getting Postgres configuration for project {project_ref}")
        response = requests.get(
            f"{self.api_base_url}/v1/projects/{project_ref}/config/database/postgres",
            headers=self.headers
        )
        return self._handle_response(response, "Get Postgres config")

    def update_postgres_config(self, project_ref: str, config: Dict) -> Dict:
        """
        Update Postgres configuration

        Args:
            project_ref: Project reference ID
            config: Configuration parameters to update

        Returns:
            Updated configuration
        """
        logger.info(f"Updating Postgres configuration for project {project_ref}")
        response = requests.put(
            f"{self.api_base_url}/v1/projects/{project_ref}/config/database/postgres",
            headers=self.headers,
            json=config
        )
        return self._handle_response(response, "Update Postgres config")

    # Authentication Management

    def get_auth_config(self, project_ref: str) -> Dict:
        """
        Get authentication configuration

        Args:
            project_ref: Project reference ID

        Returns:
            Authentication configuration
        """
        logger.info(f"Getting auth configuration for project {project_ref}")
        response = requests.get(
            f"{self.api_base_url}/v1/projects/{project_ref}/config/auth",
            headers=self.headers
        )
        return self._handle_response(response, "Get auth config")

    def update_auth_config(self, project_ref: str, config: Dict) -> Dict:
        """
        Update authentication configuration

        Args:
            project_ref: Project reference ID
            config: Configuration parameters to update

        Returns:
            Updated configuration
        """
        logger.info(f"Updating auth configuration for project {project_ref}")
        response = requests.patch(
            f"{self.api_base_url}/v1/projects/{project_ref}/config/auth",
            headers=self.headers,
            json=config
        )
        return self._handle_response(response, "Update auth config")

    # API Keys Management

    def get_api_keys(self, project_ref: str, reveal: bool = False) -> List[Dict]:
        """
        Get project API keys

        Args:
            project_ref: Project reference ID
            reveal: Whether to reveal the full API keys

        Returns:
            List of API keys
        """
        logger.info(f"Getting API keys for project {project_ref}")
        response = requests.get(
            f"{self.api_base_url}/v1/projects/{project_ref}/api-keys?reveal={str(reveal).lower()}",
            headers=self.headers
        )
        return self._handle_response(response, "Get API keys")

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Supabase Manager - Automate Supabase operations")

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Project commands
    project_parser = subparsers.add_parser("project", help="Project management commands")
    project_subparsers = project_parser.add_subparsers(dest="subcommand", help="Project subcommand")

    # List projects
    list_parser = project_subparsers.add_parser("list", help="List all projects")

    # Get project
    get_parser = project_subparsers.add_parser("get", help="Get project details")
    get_parser.add_argument("project_ref", help="Project reference ID")

    # Create project
    create_parser = project_subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("org_id", help="Organization ID")
    create_parser.add_argument("db_pass", help="Database password")
    create_parser.add_argument("--region", default="us-west-1", help="Region (default: us-west-1)")

    # Delete project
    delete_parser = project_subparsers.add_parser("delete", help="Delete a project")
    delete_parser.add_argument("project_ref", help="Project reference ID")

    # Pause project
    pause_parser = project_subparsers.add_parser("pause", help="Pause a project")
    pause_parser.add_argument("project_ref", help="Project reference ID")

    # Database commands
    db_parser = subparsers.add_parser("db", help="Database management commands")
    db_subparsers = db_parser.add_subparsers(dest="subcommand", help="Database subcommand")

    # Execute SQL
    sql_parser = db_subparsers.add_parser("sql", help="Execute SQL query")
    sql_parser.add_argument("project_ref", help="Project reference ID")
    sql_parser.add_argument("query", help="SQL query to execute")

    # Get Postgres config
    get_pg_parser = db_subparsers.add_parser("get-config", help="Get Postgres configuration")
    get_pg_parser.add_argument("project_ref", help="Project reference ID")

    # Update Postgres config
    update_pg_parser = db_subparsers.add_parser("update-config", help="Update Postgres configuration")
    update_pg_parser.add_argument("project_ref", help="Project reference ID")
    update_pg_parser.add_argument("config", help="JSON configuration string")

    # Parse arguments
    args = parser.parse_args()

    # Initialize Supabase Manager
    try:
        manager = SupabaseManager()

        # Handle commands
        if args.command == "project":
            if args.subcommand == "list":
                projects = manager.list_projects()
                print(json.dumps(projects, indent=2))
            elif args.subcommand == "get":
                project = manager.get_project(args.project_ref)
                print(json.dumps(project, indent=2))
            elif args.subcommand == "create":
                project = manager.create_project(args.name, args.org_id, args.db_pass, args.region)
                print(json.dumps(project, indent=2))
            elif args.subcommand == "delete":
                result = manager.delete_project(args.project_ref)
                print(json.dumps(result, indent=2))
            elif args.subcommand == "pause":
                result = manager.pause_project(args.project_ref)
                print(json.dumps(result, indent=2))
        elif args.command == "db":
            if args.subcommand == "sql":
                result = manager.execute_sql(args.project_ref, args.query)
                print(json.dumps(result, indent=2))
            elif args.subcommand == "get-config":
                config = manager.get_postgres_config(args.project_ref)
                print(json.dumps(config, indent=2))
            elif args.subcommand == "update-config":
                config_dict = json.loads(args.config)
                result = manager.update_postgres_config(args.project_ref, config_dict)
                print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

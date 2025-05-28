#!/usr/bin/env python
"""
Supabase Project Manager

This script provides utilities for managing Supabase projects,
including creating, listing, pausing, and resuming projects.

Usage:
    python -m scripts.supabase_project [command] [options]

Commands:
    list        - List all projects
    get         - Get project details
    create      - Create a new project
    pause       - Pause a project
    resume      - Resume a paused project
    setup       - Set up a project with schema and initial data
"""

import os
import sys
import json
import logging
import argparse
import requests
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("supabase-project")

class SupabaseProjectManager:
    """Supabase Project Manager"""

    def __init__(self, access_token: str = None):
        """
        Initialize the Supabase Project Manager

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

        logger.info("Supabase Project Manager initialized")

    def _handle_response(self, response: requests.Response, operation: str) -> Dict:
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
                return {}
            return response.json()
        else:
            error_message = f"{operation} failed: {response.status_code} - {response.text}"
            logger.error(error_message)
            raise Exception(error_message)

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

    def resume_project(self, project_ref: str) -> Dict:
        """
        Resume a paused project

        Args:
            project_ref: Project reference ID

        Returns:
            Resume result
        """
        logger.info(f"Resuming project {project_ref}")

        # Note: There's no direct "resume" endpoint in the Supabase API
        # Instead, we need to restore the project
        response = requests.post(
            f"{self.api_base_url}/v1/projects/{project_ref}/restore",
            headers=self.headers
        )

        return self._handle_response(response, "Resume project")

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

    def setup_project(self, project_ref: str, schema_file: str) -> bool:
        """
        Set up a project with schema and initial data

        Args:
            project_ref: Project reference ID
            schema_file: Path to SQL schema file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Setting up project {project_ref} with schema from {schema_file}")

            # Read schema file
            with open(schema_file, 'r') as f:
                schema_sql = f.read()

            # Execute schema SQL
            self.execute_sql(project_ref, schema_sql)

            logger.info(f"Project {project_ref} set up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set up project: {str(e)}")
            return False

    def wait_for_project_active(self, project_ref: str, timeout: int = 300, interval: int = 5) -> bool:
        """
        Wait for a project to become active

        Args:
            project_ref: Project reference ID
            timeout: Maximum time to wait in seconds (default: 300)
            interval: Check interval in seconds (default: 5)

        Returns:
            True if project becomes active, False if timeout
        """
        logger.info(f"Waiting for project {project_ref} to become active")

        start_time = time.time()
        while time.time() - start_time < timeout:
            project = self.get_project(project_ref)
            if project.get("status") == "ACTIVE_HEALTHY":
                logger.info(f"Project {project_ref} is now active")
                return True

            logger.info(f"Project status: {project.get('status')}. Waiting {interval} seconds...")
            time.sleep(interval)

        logger.error(f"Timeout waiting for project {project_ref} to become active")
        return False

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Supabase Project Manager")

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List projects command
    list_parser = subparsers.add_parser("list", help="List all projects")

    # Get project command
    get_parser = subparsers.add_parser("get", help="Get project details")
    get_parser.add_argument("project_ref", help="Project reference ID")

    # Create project command
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("org_id", help="Organization ID")
    create_parser.add_argument("db_pass", help="Database password")
    create_parser.add_argument("--region", default="us-west-1", help="Region (default: us-west-1)")
    create_parser.add_argument("--wait", action="store_true", help="Wait for the project to become active")

    # Pause project command
    pause_parser = subparsers.add_parser("pause", help="Pause a project")
    pause_parser.add_argument("project_ref", help="Project reference ID")

    # Resume project command
    resume_parser = subparsers.add_parser("resume", help="Resume a paused project")
    resume_parser.add_argument("project_ref", help="Project reference ID")
    resume_parser.add_argument("--wait", action="store_true", help="Wait for the project to become active")

    # Setup project command
    setup_parser = subparsers.add_parser("setup", help="Set up a project with schema and initial data")
    setup_parser.add_argument("project_ref", help="Project reference ID")
    setup_parser.add_argument("schema_file", help="Path to SQL schema file")

    # Parse arguments
    args = parser.parse_args()

    # Initialize Supabase Project Manager
    try:
        manager = SupabaseProjectManager()

        # Handle commands
        if args.command == "list":
            projects = manager.list_projects()
            print(json.dumps(projects, indent=2))

        elif args.command == "get":
            project = manager.get_project(args.project_ref)
            print(json.dumps(project, indent=2))

        elif args.command == "create":
            project = manager.create_project(args.name, args.org_id, args.db_pass, args.region)
            print(json.dumps(project, indent=2))

            if args.wait:
                manager.wait_for_project_active(project["id"])

        elif args.command == "pause":
            result = manager.pause_project(args.project_ref)
            print(json.dumps(result, indent=2))

        elif args.command == "resume":
            result = manager.resume_project(args.project_ref)
            print(json.dumps(result, indent=2))

            if args.wait:
                manager.wait_for_project_active(args.project_ref)

        elif args.command == "setup":
            success = manager.setup_project(args.project_ref, args.schema_file)
            if success:
                print(f"Project {args.project_ref} set up successfully")
            else:
                print(f"Failed to set up project {args.project_ref}")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

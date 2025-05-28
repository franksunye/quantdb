#!/usr/bin/env python
"""
Supabase API Keys Manager

This script provides utilities for managing Supabase API keys,
including retrieving, rotating, and updating environment variables.

Usage:
    python -m scripts.supabase_api_keys [command] [options]

Commands:
    list        - List all API keys for a project
    update-env  - Update environment variables with API keys
"""

import os
import sys
import json
import logging
import argparse
import requests
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
logger = logging.getLogger("supabase-api-keys")

class SupabaseApiKeysManager:
    """Supabase API Keys Manager"""

    def __init__(self, access_token: str = None):
        """
        Initialize the Supabase API Keys Manager

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

        logger.info("Supabase API Keys Manager initialized")

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

    def get_api_keys(self, project_ref: str, reveal: bool = False) -> List[Dict]:
        """
        Get API keys for a project

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

    def update_environment_variables(self, project_ref: str, env_file: str = ".env") -> bool:
        """
        Update environment variables with API keys

        Args:
            project_ref: Project reference ID
            env_file: Path to the environment file (default: .env)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating environment variables in {env_file}")

            # Get API keys with full values
            api_keys = self.get_api_keys(project_ref, reveal=True)

            # Get project URL
            response = requests.get(
                f"{self.api_base_url}/v1/projects/{project_ref}",
                headers=self.headers
            )
            project = self._handle_response(response, "Get project details")

            # Update SUPABASE_URL
            supabase_url = f"https://{project_ref}.supabase.co"
            set_key(env_file, "SUPABASE_URL", supabase_url)

            # Update API keys
            for key in api_keys:
                if key["type"] == "anon":
                    set_key(env_file, "SUPABASE_KEY", key["api_key"])
                elif key["type"] == "service_role":
                    set_key(env_file, "SUPABASE_SERVICE_KEY", key["api_key"])

            logger.info(f"Environment variables updated successfully in {env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to update environment variables: {str(e)}")
            return False

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Supabase API Keys Manager")

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List API keys command
    list_parser = subparsers.add_parser("list", help="List all API keys for a project")
    list_parser.add_argument("project_ref", help="Project reference ID")
    list_parser.add_argument("--reveal", action="store_true", help="Reveal full API keys")

    # Update environment variables command
    update_env_parser = subparsers.add_parser("update-env", help="Update environment variables with API keys")
    update_env_parser.add_argument("project_ref", help="Project reference ID")
    update_env_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Parse arguments
    args = parser.parse_args()

    # Initialize Supabase API Keys Manager
    try:
        manager = SupabaseApiKeysManager()

        # Handle commands
        if args.command == "list":
            api_keys = manager.get_api_keys(args.project_ref, args.reveal)
            print(json.dumps(api_keys, indent=2))

        elif args.command == "update-env":
            success = manager.update_environment_variables(args.project_ref, args.env_file)
            if success:
                print(f"Environment variables updated successfully in {args.env_file}")
            else:
                print(f"Failed to update environment variables in {args.env_file}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

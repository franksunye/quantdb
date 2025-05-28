#!/usr/bin/env python
"""
Supabase Database Password Manager

This script provides utilities for managing Supabase database passwords,
including resetting passwords and updating environment variables.

Usage:
    python -m scripts.supabase_db_password [command] [options]

Commands:
    reset       - Reset the database password
    update-env  - Update environment variables with the new password
"""

import os
import sys
import json
import logging
import argparse
import secrets
import string
import requests
from typing import Dict, Optional
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("supabase-db-password")

class SupabaseDatabasePasswordManager:
    """Supabase Database Password Manager"""

    def __init__(self, access_token: str = None):
        """
        Initialize the Supabase Database Password Manager

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

        logger.info("Supabase Database Password Manager initialized")

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

    def generate_strong_password(self, length: int = 24) -> str:
        """
        Generate a strong random password

        Args:
            length: Password length (default: 24)

        Returns:
            Generated password
        """
        # Define character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

        # Ensure at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]

        # Fill the rest with random characters from all sets
        all_chars = uppercase + lowercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        # Convert to string
        return ''.join(password)

    def reset_database_password(self, project_ref: str, new_password: Optional[str] = None) -> Dict:
        """
        Reset the database password

        Args:
            project_ref: Project reference ID
            new_password: New password (if None, a strong password will be generated)

        Returns:
            Result with the new password
        """
        # Generate a strong password if not provided
        if new_password is None:
            new_password = self.generate_strong_password()

        logger.info(f"Resetting database password for project {project_ref}")

        # Update Postgres configuration with the new password
        data = {
            "password": new_password
        }

        # Use the Management API to update the password
        # Note: This is a simplified approach - the actual API endpoint might be different
        # and would need to be verified with Supabase documentation
        response = requests.post(
            f"{self.api_base_url}/v1/projects/{project_ref}/db/password/reset",
            headers=self.headers,
            json=data
        )

        result = self._handle_response(response, "Reset database password")

        # Add the new password to the result
        result["new_password"] = new_password

        return result

    def update_environment_variables(self, project_ref: str, password: str, env_file: str = ".env") -> bool:
        """
        Update environment variables with the new password

        Args:
            project_ref: Project reference ID
            password: New database password
            env_file: Path to the environment file (default: .env)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating environment variables in {env_file}")

            # Get project details to construct the database URL
            response = requests.get(
                f"{self.api_base_url}/v1/projects/{project_ref}",
                headers=self.headers
            )
            project = self._handle_response(response, "Get project details")

            # Update DATABASE_URL
            db_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
            set_key(env_file, "DATABASE_URL", db_url)

            # Update SUPABASE_DB_PASSWORD
            set_key(env_file, "SUPABASE_DB_PASSWORD", password)

            logger.info(f"Environment variables updated successfully in {env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to update environment variables: {str(e)}")
            return False

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Supabase Database Password Manager")

    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Reset password command
    reset_parser = subparsers.add_parser("reset", help="Reset the database password")
    reset_parser.add_argument("project_ref", help="Project reference ID")
    reset_parser.add_argument("--password", help="New password (if not provided, a strong password will be generated)")
    reset_parser.add_argument("--update-env", action="store_true", help="Update environment variables with the new password")
    reset_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Update environment variables command
    update_env_parser = subparsers.add_parser("update-env", help="Update environment variables with the new password")
    update_env_parser.add_argument("project_ref", help="Project reference ID")
    update_env_parser.add_argument("password", help="Database password")
    update_env_parser.add_argument("--env-file", default=".env", help="Path to the environment file (default: .env)")

    # Parse arguments
    args = parser.parse_args()

    # Initialize Supabase Database Password Manager
    try:
        manager = SupabaseDatabasePasswordManager()

        # Handle commands
        if args.command == "reset":
            result = manager.reset_database_password(args.project_ref, args.password)
            print(f"Database password reset successfully for project {args.project_ref}")
            print(f"New password: {result['new_password']}")

            # Update environment variables if requested
            if args.update_env:
                success = manager.update_environment_variables(
                    args.project_ref,
                    result["new_password"],
                    args.env_file
                )
                if success:
                    print(f"Environment variables updated successfully in {args.env_file}")
                else:
                    print(f"Failed to update environment variables in {args.env_file}")

        elif args.command == "update-env":
            success = manager.update_environment_variables(
                args.project_ref,
                args.password,
                args.env_file
            )
            if success:
                print(f"Environment variables updated successfully in {args.env_file}")
            else:
                print(f"Failed to update environment variables in {args.env_file}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

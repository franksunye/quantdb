#!/usr/bin/env python
"""
Test Supabase Management API Connection

This script tests the connection to the Supabase Management API using the service role key.
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test-supabase-management-api")

def test_management_api():
    """Test connection to Supabase Management API"""
    # Load environment variables
    load_dotenv()

    # Get Supabase URL and keys
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase_access_token = os.getenv('SUPABASE_ACCESS_TOKEN')

    if not supabase_url:
        logger.error("Missing Supabase URL environment variable")
        return False

    # Check if we have a personal access token
    if not supabase_access_token:
        logger.error("Missing SUPABASE_ACCESS_TOKEN environment variable")
        logger.error("The Supabase Management API requires a personal access token (PAT)")
        logger.error("You can create one at https://app.supabase.com/account/tokens")
        logger.error("Then add it to your .env file as SUPABASE_ACCESS_TOKEN=your_token")

        # Try with service key anyway for testing
        logger.warning("Trying with SUPABASE_SERVICE_KEY instead, but this will likely fail")
        token = supabase_service_key
    else:
        logger.info("Using SUPABASE_ACCESS_TOKEN for Management API")
        token = supabase_access_token

    logger.info(f"Supabase URL: {supabase_url}")
    if token:
        logger.info(f"Token: {token[:10]}...")

    # Extract project ID from URL
    project_id = supabase_url.split('//')[1].split('.')[0]
    logger.info(f"Project ID: {project_id}")

    # Test Management API connection
    try:
        logger.info("Testing Management API connection...")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"https://api.supabase.com/v1/projects/{project_id}",
            headers=headers
        )

        logger.info(f"Management API Response: {response.status_code}")
        if response.status_code == 200:
            logger.info("Management API connection successful")
            logger.info(f"Project details: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logger.error(f"Management API connection failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Management API connection error: {str(e)}")
        return False

def test_execute_sql():
    """Test executing SQL query"""
    # Load environment variables
    load_dotenv()

    # Get Supabase URL and keys
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase_access_token = os.getenv('SUPABASE_ACCESS_TOKEN')

    if not supabase_url:
        logger.error("Missing Supabase URL environment variable")
        return False

    # Check if we have a personal access token
    if not supabase_access_token:
        logger.error("Missing SUPABASE_ACCESS_TOKEN environment variable")
        logger.error("The Supabase Management API requires a personal access token (PAT)")
        logger.error("You can create one at https://app.supabase.com/account/tokens")

        # Try with service key anyway for testing
        logger.warning("Trying with SUPABASE_SERVICE_KEY instead, but this will likely fail")
        token = supabase_service_key
    else:
        logger.info("Using SUPABASE_ACCESS_TOKEN for Management API")
        token = supabase_access_token

    # Extract project ID from URL
    project_id = supabase_url.split('//')[1].split('.')[0]

    # Test SQL execution
    try:
        logger.info("Testing SQL execution...")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        sql_query = "SELECT NOW();"

        # The correct endpoint for SQL execution is /database/query
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{project_id}/database/query",
            headers=headers,
            json={"query": sql_query}
        )

        logger.info(f"SQL Execution Response: {response.status_code}")
        if response.status_code == 200 or response.status_code == 201:
            logger.info("SQL execution successful")
            logger.info(f"Result: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logger.error(f"SQL execution failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return False

def test_list_projects():
    """Test listing all projects"""
    # Load environment variables
    load_dotenv()

    # Get Supabase keys
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase_access_token = os.getenv('SUPABASE_ACCESS_TOKEN')

    # Check if we have a personal access token
    if not supabase_access_token:
        logger.error("Missing SUPABASE_ACCESS_TOKEN environment variable")
        logger.error("The Supabase Management API requires a personal access token (PAT)")
        logger.error("You can create one at https://app.supabase.com/account/tokens")

        # Try with service key anyway for testing
        logger.warning("Trying with SUPABASE_SERVICE_KEY instead, but this will likely fail")
        token = supabase_service_key
    else:
        logger.info("Using SUPABASE_ACCESS_TOKEN for Management API")
        token = supabase_access_token

    if not token:
        logger.error("No authentication token available")
        return False

    # Test listing projects
    try:
        logger.info("Testing listing projects...")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            "https://api.supabase.com/v1/projects",
            headers=headers
        )

        logger.info(f"List Projects Response: {response.status_code}")
        if response.status_code == 200:
            logger.info("Listing projects successful")
            projects = response.json()
            logger.info(f"Number of projects: {len(projects)}")
            for project in projects:
                logger.info(f"Project: {project.get('name')} (ID: {project.get('id')})")
            return True
        else:
            logger.error(f"Listing projects failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Listing projects error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing Supabase Management API...")

    # Test Management API connection
    api_success = test_management_api()

    # Test SQL execution
    sql_success = test_execute_sql()

    # Test listing projects
    projects_success = test_list_projects()

    # Check overall success
    if api_success and sql_success and projects_success:
        logger.info("All tests passed successfully")
        sys.exit(0)
    else:
        logger.error("Some tests failed")
        sys.exit(1)

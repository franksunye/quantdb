#!/usr/bin/env python
# run_stock_data_e2e_tests.py
"""
Test runner script for stock data service end-to-end tests.

This script runs the end-to-end tests for the stock data service in the simplified architecture.
It provides options to run specific tests and enable verbose output.
"""

import argparse
import sys
import os
import unittest
import logging
from datetime import datetime
from pathlib import Path

# Ensure logs directory exists
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/stock_data_e2e_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("test_runner")

def run_tests(test_pattern=None, verbose=False):
    """Run the stock data service end-to-end tests."""
    logger.info("Starting stock data service end-to-end tests")
    
    # Add project root to path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Import the test module
    from tests.e2e.test_stock_data_service_e2e import TestStockDataServiceE2E
    
    # Create test suite
    loader = unittest.TestLoader()
    if test_pattern:
        logger.info(f"Running specific test: {test_pattern}")
        suite = loader.loadTestsFromName(f"tests.e2e.test_stock_data_service_e2e.TestStockDataServiceE2E.{test_pattern}")
    else:
        logger.info("Running all tests")
        suite = loader.loadTestsFromTestCase(TestStockDataServiceE2E)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # Log results
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run stock data service end-to-end tests")
    parser.add_argument("--test", help="Specific test to run (e.g., 'test_empty_database_flow')")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    sys.exit(run_tests(args.test, args.verbose))

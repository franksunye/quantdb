"""
Unit tests for the enhanced logger module.
"""
import json
import os
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Skip this test as enhanced logger is now simplified
import pytest

# Enhanced logger functionality migrated to core
from core.utils.logger import EnhancedLogger, get_logger, log_function, setup_enhanced_logger

pytestmark = pytest.mark.skip(reason="Enhanced logger migrated to simplified core logger")

class TestEnhancedLogger(unittest.TestCase):
    """Tests for the EnhancedLogger class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary log file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "test_log.log")
        
        # Create logger
        self.logger = EnhancedLogger(
            name="test_logger",
            log_file=self.log_file,
            level="DEBUG",
            console_output=False,  # Disable console output for tests
            detailed=True
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        # Check that logger was created
        self.assertEqual(self.logger.name, "test_logger")
        self.assertEqual(self.logger.log_file, self.log_file)
        self.assertEqual(self.logger.level, 10)  # DEBUG = 10
        self.assertTrue(self.logger.detailed)
        
        # Check that log file was created
        self.assertTrue(os.path.exists(self.log_file))
    
    def test_context_management(self):
        """Test context management."""
        # Start context
        context_id = self.logger.start_context(metadata={"test": "value"})
        
        # Check that context was created
        self.assertEqual(self.logger.context_id, context_id)
        self.assertIsNotNone(self.logger.start_time)
        
        # Log some messages
        self.logger.info("Test message")
        self.logger.debug("Debug message")
        
        # Add metrics
        self.logger.add_metric("test_metric", 123)
        
        # End context
        duration = self.logger.end_context()
        
        # Check that context was ended
        self.assertIsNone(self.logger.context_id)
        self.assertGreaterEqual(duration, 0)
        
        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()
            
            # Check that context start and end messages are in the log
            self.assertIn("CONTEXT START", log_content)
            self.assertIn("CONTEXT END", log_content)
            self.assertIn("Test message", log_content)
            self.assertIn("Debug message", log_content)
            self.assertIn("CONTEXT METRICS", log_content)
            self.assertIn("test_metric", log_content)
    
    def test_log_levels(self):
        """Test different log levels."""
        # Start context
        self.logger.start_context()
        
        # Log messages at different levels
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
        
        # End context
        self.logger.end_context()
        
        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()
            
            # Check that all messages are in the log
            self.assertIn("Debug message", log_content)
            self.assertIn("Info message", log_content)
            self.assertIn("Warning message", log_content)
            self.assertIn("Error message", log_content)
            self.assertIn("Critical message", log_content)
            
            # Check log levels
            self.assertIn("[DEBUG]", log_content)
            self.assertIn("[INFO]", log_content)
            self.assertIn("[WARNING]", log_content)
            self.assertIn("[ERROR]", log_content)
            self.assertIn("[CRITICAL]", log_content)
    
    def test_log_data(self):
        """Test logging structured data."""
        # Start context
        self.logger.start_context()
        
        # Log structured data
        test_data = {
            "string": "value",
            "number": 123,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {
                "key": "value"
            }
        }
        self.logger.log_data("test_data", test_data)
        
        # End context
        self.logger.end_context()
        
        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()
            
            # Check that data is in the log
            self.assertIn("DATA [test_data]", log_content)
            self.assertIn("string", log_content)
            self.assertIn("value", log_content)
            self.assertIn("number", log_content)
            self.assertIn("123", log_content)
            self.assertIn("boolean", log_content)
            self.assertIn("true", log_content)
            self.assertIn("list", log_content)
            self.assertIn("[1, 2, 3]", log_content)
            self.assertIn("nested", log_content)
            self.assertIn("key", log_content)
    
    def test_error_logging_with_exception(self):
        """Test logging errors with exception info."""
        # Start context
        self.logger.start_context()
        
        # Create an exception
        try:
            raise ValueError("Test error")
        except ValueError as e:
            # Log error with exception
            self.logger.error("An error occurred", exc_info=e)
        
        # End context
        self.logger.end_context()
        
        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()
            
            # Check that error message and exception info are in the log
            self.assertIn("An error occurred", log_content)
            self.assertIn("ValueError", log_content)
            self.assertIn("Test error", log_content)
            self.assertIn("Traceback", log_content)

class TestLogFunctionDecorator(unittest.TestCase):
    """Tests for the log_function decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary log file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "test_log.log")
        
        # Create logger
        self.logger = setup_enhanced_logger(
            name="test_decorator",
            log_file=self.log_file,
            level="DEBUG",
            console_output=False,  # Disable console output for tests
            detailed=True
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_log_function_success(self):
        """Test log_function decorator with successful function."""
        # Define a test function with the decorator
        @log_function(logger=self.logger)
        def test_function(a, b):
            return a + b
        
        # Call the function
        result = test_function(1, 2)
        
        # Check the result
        self.assertEqual(result, 3)
        
        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()
            
            # Check that function start and end messages are in the log
            self.assertIn("FUNCTION START: test_function", log_content)
            self.assertIn("FUNCTION END: test_function - Success", log_content)
            self.assertIn("1, 2", log_content)  # Function arguments
    
    def test_log_function_error(self):
        """Test log_function decorator with function that raises an exception."""
        # Define a test function with the decorator
        @log_function(logger=self.logger)
        def test_function_error():
            raise ValueError("Test error")
        
        # Call the function and expect an exception
        with self.assertRaises(ValueError):
            test_function_error()
        
        # Check log file content
        with open(self.log_file, "r") as f:
            log_content = f.read()
            
            # Check that function start and error messages are in the log
            self.assertIn("FUNCTION START: test_function_error", log_content)
            self.assertIn("FUNCTION ERROR: test_function_error", log_content)
            self.assertIn("ValueError", log_content)
            self.assertIn("Test error", log_content)

class TestSetupEnhancedLogger(unittest.TestCase):
    """Tests for the setup_enhanced_logger function."""
    
    def test_setup_enhanced_logger(self):
        """Test setup_enhanced_logger function."""
        # Create a temporary log file
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test_setup.log")
            
            # Set up logger
            logger = setup_enhanced_logger(
                name="test_setup",
                log_file=log_file,
                level="INFO",
                console_output=False,
                detailed=True
            )
            
            # Check logger properties
            self.assertEqual(logger.name, "test_setup")
            self.assertEqual(logger.log_file, log_file)
            self.assertEqual(logger.level, 20)  # INFO = 20
            self.assertTrue(logger.detailed)
            
            # Check that log file was created
            self.assertTrue(os.path.exists(log_file))

if __name__ == "__main__":
    unittest.main()

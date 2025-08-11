"""
Unit tests for the error handling module.
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError

# Import error handlers from api.errors
from api.errors import (
    ErrorCode,
    QuantDBException,
    DataNotFoundException,
    DataFetchException,
    AKShareException,
    DatabaseException,
    MCPProcessingException,
    create_error_response,
    quantdb_exception_handler,
    validation_exception_handler,
    global_exception_handler,
    register_exception_handlers
)

# Error handling migrated to API middleware
import pytest
pytestmark = pytest.mark.skip(reason="Error handling migrated to API middleware")

class TestErrorCodes(unittest.TestCase):
    """Tests for the ErrorCode class."""

    def test_error_codes_exist(self):
        """Test that error codes exist."""
        self.assertEqual(ErrorCode.INTERNAL_ERROR, "INTERNAL_ERROR")
        self.assertEqual(ErrorCode.VALIDATION_ERROR, "VALIDATION_ERROR")
        self.assertEqual(ErrorCode.NOT_FOUND, "NOT_FOUND")
        self.assertEqual(ErrorCode.BAD_REQUEST, "BAD_REQUEST")
        self.assertEqual(ErrorCode.DATA_NOT_FOUND, "DATA_NOT_FOUND")
        self.assertEqual(ErrorCode.DATA_FETCH_ERROR, "DATA_FETCH_ERROR")
        self.assertEqual(ErrorCode.AKSHARE_ERROR, "AKSHARE_ERROR")
        self.assertEqual(ErrorCode.DATABASE_ERROR, "DATABASE_ERROR")
        self.assertEqual(ErrorCode.MCP_PROCESSING_ERROR, "MCP_PROCESSING_ERROR")

class TestQuantDBException(unittest.TestCase):
    """Tests for the QuantDBException class."""

    def test_base_exception(self):
        """Test the base QuantDBException."""
        # Create exception
        exc = QuantDBException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"test": "value"}
        )

        # Check properties
        self.assertEqual(exc.message, "Test error")
        self.assertEqual(exc.error_code, "TEST_ERROR")
        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.details, {"test": "value"})
        self.assertIsNotNone(exc.timestamp)

        # Check string representation
        self.assertEqual(str(exc), "Test error")

    def test_default_values(self):
        """Test default values for QuantDBException."""
        # Create exception with minimal parameters
        exc = QuantDBException(message="Test error")

        # Check default properties
        self.assertEqual(exc.message, "Test error")
        self.assertEqual(exc.error_code, ErrorCode.INTERNAL_ERROR)
        self.assertEqual(exc.status_code, 500)
        self.assertEqual(exc.details, {})
        self.assertIsNotNone(exc.timestamp)

class TestSpecificExceptions(unittest.TestCase):
    """Tests for specific exception classes."""

    def test_data_not_found_exception(self):
        """Test DataNotFoundException."""
        # Create exception
        exc = DataNotFoundException(
            message="Data not found",
            details={"symbol": "AAPL"}
        )

        # Check properties
        self.assertEqual(exc.message, "Data not found")
        self.assertEqual(exc.error_code, ErrorCode.DATA_NOT_FOUND)
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.details, {"symbol": "AAPL"})

    def test_data_fetch_exception(self):
        """Test DataFetchException."""
        # Create exception
        exc = DataFetchException(
            message="Error fetching data",
            details={"source": "AKShare"}
        )

        # Check properties
        self.assertEqual(exc.message, "Error fetching data")
        self.assertEqual(exc.error_code, ErrorCode.DATA_FETCH_ERROR)
        self.assertEqual(exc.status_code, 502)
        self.assertEqual(exc.details, {"source": "AKShare"})

    def test_akshare_exception(self):
        """Test AKShareException."""
        # Create exception
        exc = AKShareException(
            message="AKShare error",
            details={"function": "stock_zh_a_hist"}
        )

        # Check properties
        self.assertEqual(exc.message, "AKShare error")
        self.assertEqual(exc.error_code, ErrorCode.AKSHARE_ERROR)
        self.assertEqual(exc.status_code, 502)
        self.assertEqual(exc.details, {"function": "stock_zh_a_hist"})

    def test_database_exception(self):
        """Test DatabaseException."""
        # Create exception
        exc = DatabaseException(
            message="Database error",
            details={"table": "prices"}
        )

        # Check properties
        self.assertEqual(exc.message, "Database error")
        self.assertEqual(exc.error_code, ErrorCode.DATABASE_ERROR)
        self.assertEqual(exc.status_code, 500)
        self.assertEqual(exc.details, {"table": "prices"})

    def test_mcp_processing_exception(self):
        """Test MCPProcessingException."""
        # Create exception
        exc = MCPProcessingException(
            message="MCP processing error",
            details={"query": "What is the price of AAPL?"}
        )

        # Check properties
        self.assertEqual(exc.message, "MCP processing error")
        self.assertEqual(exc.error_code, ErrorCode.MCP_PROCESSING_ERROR)
        self.assertEqual(exc.status_code, 500)
        self.assertEqual(exc.details, {"query": "What is the price of AAPL?"})

class TestErrorResponse(unittest.TestCase):
    """Tests for the create_error_response function."""

    def test_create_error_response(self):
        """Test create_error_response function."""
        # Create error response
        response = create_error_response(
            error_code="TEST_ERROR",
            message="Test error",
            status_code=400,
            details={"test": "value"},
            path="/api/test"
        )

        # Check response structure
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], "TEST_ERROR")
        self.assertEqual(response["error"]["message"], "Test error")
        self.assertEqual(response["error"]["status_code"], 400)
        self.assertEqual(response["error"]["details"], {"test": "value"})
        self.assertEqual(response["error"]["path"], "/api/test")
        self.assertIn("timestamp", response["error"])

    def test_create_error_response_minimal(self):
        """Test create_error_response with minimal parameters."""
        # Create error response with minimal parameters
        response = create_error_response(
            error_code="TEST_ERROR",
            message="Test error",
            status_code=400
        )

        # Check response structure
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], "TEST_ERROR")
        self.assertEqual(response["error"]["message"], "Test error")
        self.assertEqual(response["error"]["status_code"], 400)
        self.assertEqual(response["error"]["details"], {})
        self.assertIsNone(response["error"]["path"])
        self.assertIn("timestamp", response["error"])

class TestExceptionHandlers(unittest.TestCase):
    """Tests for exception handlers."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock request
        self.mock_request = MagicMock(spec=Request)
        self.mock_request.url.path = "/api/test"

    @patch("api.errors.logger")
    def test_quantdb_exception_handler(self, mock_logger):
        """Test quantdb_exception_handler."""
        # Create exception
        exc = QuantDBException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"test": "value"}
        )

        # We can't directly test the async handler in a synchronous test
        # So we'll just check that the handler exists and has the right signature
        self.assertTrue(callable(quantdb_exception_handler))

        # Check that the handler takes the right arguments
        import inspect
        sig = inspect.signature(quantdb_exception_handler)
        self.assertEqual(len(sig.parameters), 2)
        self.assertIn("request", sig.parameters)
        self.assertIn("exc", sig.parameters)

    @patch("api.errors.logger")
    def test_validation_exception_handler(self, mock_logger):
        """Test validation_exception_handler."""
        # Create validation error
        class TestModel(BaseModel):
            name: str = Field(..., min_length=3)

        try:
            TestModel(name="a")
            self.fail("ValidationError not raised")
        except ValidationError as exc:
            # We can't directly test the async handler in a synchronous test
            # So we'll just check that the handler exists and has the right signature
            self.assertTrue(callable(validation_exception_handler))

            # Check that the handler takes the right arguments
            import inspect
            sig = inspect.signature(validation_exception_handler)
            self.assertEqual(len(sig.parameters), 2)
            self.assertIn("request", sig.parameters)
            self.assertIn("exc", sig.parameters)

class TestRegisterExceptionHandlers(unittest.TestCase):
    """Tests for register_exception_handlers function."""

    def test_register_exception_handlers(self):
        """Test register_exception_handlers function."""
        # Create mock app
        mock_app = MagicMock(spec=FastAPI)

        # Call function
        register_exception_handlers(mock_app)

        # Check that app.add_exception_handler was called for each handler
        self.assertGreaterEqual(mock_app.add_exception_handler.call_count, 4)

        # Check that handlers were registered for the correct exception types
        mock_app.add_exception_handler.assert_any_call(QuantDBException, quantdb_exception_handler)
        mock_app.add_exception_handler.assert_any_call(RequestValidationError, validation_exception_handler)
        mock_app.add_exception_handler.assert_any_call(ValidationError, validation_exception_handler)
        mock_app.add_exception_handler.assert_any_call(Exception, global_exception_handler)

if __name__ == "__main__":
    unittest.main()

"""
Performance tests for the API.

This module tests the performance of the API endpoints.
"""
import unittest
import time
import statistics
from fastapi.testclient import TestClient

from src.api.main import app
from src.config import API_PREFIX
from src.enhanced_logger import setup_enhanced_logger

# Setup logger
logger = setup_enhanced_logger(__name__)

# Create test client
client = TestClient(app)


class TestAPIPerformance(unittest.TestCase):
    """Performance tests for the API."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Number of requests to make for each test
        self.num_requests = 10
        
        # Acceptable response time thresholds (in seconds)
        self.fast_threshold = 0.1  # For simple endpoints
        self.medium_threshold = 0.5  # For endpoints with database queries
        self.slow_threshold = 2.0  # For endpoints with external API calls
    
    def measure_response_time(self, url, method="get", data=None, expected_status=200):
        """
        Measure the response time of an API endpoint.
        
        Args:
            url: The URL to request
            method: The HTTP method to use (default: "get")
            data: The data to send (default: None)
            expected_status: The expected status code (default: 200)
            
        Returns:
            The response time in seconds
        """
        # Get the appropriate request method
        request_method = getattr(client, method.lower())
        
        # Start timer
        start_time = time.time()
        
        # Make request
        if method.lower() in ["post", "put", "patch"] and data is not None:
            response = request_method(url, json=data)
        else:
            response = request_method(url)
        
        # End timer
        end_time = time.time()
        
        # Calculate response time
        response_time = end_time - start_time
        
        # Check status code
        self.assertEqual(response.status_code, expected_status)
        
        return response_time
    
    def test_root_endpoint_performance(self):
        """Test the performance of the root endpoint."""
        # Measure response times for multiple requests
        response_times = []
        for _ in range(self.num_requests):
            response_time = self.measure_response_time("/")
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Root endpoint performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.fast_threshold)
    
    def test_health_endpoint_performance(self):
        """Test the performance of the health endpoint."""
        # Measure response times for multiple requests
        response_times = []
        for _ in range(self.num_requests):
            response_time = self.measure_response_time(f"{API_PREFIX}/health")
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Health endpoint performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.fast_threshold)
    
    def test_version_info_endpoint_performance(self):
        """Test the performance of the version info endpoint."""
        # Measure response times for multiple requests
        response_times = []
        for _ in range(self.num_requests):
            response_time = self.measure_response_time(f"{API_PREFIX}/version/info")
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Version info endpoint performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.fast_threshold)
    
    def test_assets_list_endpoint_performance(self):
        """Test the performance of the assets list endpoint."""
        # Measure response times for multiple requests
        response_times = []
        for _ in range(self.num_requests):
            response_time = self.measure_response_time(f"{API_PREFIX}/assets/")
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Assets list endpoint performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.medium_threshold)
    
    def test_historical_data_endpoint_performance(self):
        """Test the performance of the historical data endpoint."""
        # Measure response times for multiple requests
        response_times = []
        for _ in range(self.num_requests):
            url = f"{API_PREFIX}/historical/stock/000001"
            params = {
                "start_date": "2025-04-01",
                "end_date": "2025-04-30"
            }
            
            # Start timer
            start_time = time.time()
            
            # Make request
            response = client.get(url, params=params)
            
            # End timer
            end_time = time.time()
            
            # Calculate response time
            response_time = end_time - start_time
            
            # Check status code (accept 200, 404, or 400)
            self.assertIn(response.status_code, [200, 404, 400])
            
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Historical data endpoint performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.slow_threshold)
    
    def test_error_handling_performance(self):
        """Test the performance of error handling."""
        # Measure response times for multiple requests to non-existent endpoint
        response_times = []
        for _ in range(self.num_requests):
            response_time = self.measure_response_time(
                "/nonexistent-endpoint",
                expected_status=404
            )
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Error handling performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.fast_threshold)
    
    def test_validation_error_performance(self):
        """Test the performance of validation error handling."""
        # Measure response times for multiple requests with invalid data
        response_times = []
        for _ in range(self.num_requests):
            response_time = self.measure_response_time(
                f"{API_PREFIX}/mcp/query",
                method="post",
                data={},  # Missing required fields
                expected_status=422
            )
            response_times.append(response_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Log results
        logger.info(f"Validation error performance:")
        logger.info(f"  Average: {avg_time:.4f}s")
        logger.info(f"  Maximum: {max_time:.4f}s")
        logger.info(f"  Minimum: {min_time:.4f}s")
        
        # Assert that the average response time is below the threshold
        self.assertLess(avg_time, self.medium_threshold)


if __name__ == "__main__":
    unittest.main()

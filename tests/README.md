# QuantDB Test Structure

This directory contains tests for the QuantDB project. The tests are organized into the following directories:

## Test Directories

### `/tests/unit`

Unit tests focus on testing individual components in isolation. These tests should be fast and not depend on external services.

- `test_cache_engine.py`: Tests for the cache engine component
- `test_freshness_tracker.py`: Tests for the freshness tracker component

### `/tests/integration`

Integration tests focus on testing how components work together. These tests may involve multiple components and may depend on external services.

- `test_cache_api.py`: Tests for the cache API endpoints
- `test_cache_integration.py`: Tests for the integration between cache engine and freshness tracker

### `/tests/api`

API tests focus on testing the API endpoints. These tests may involve making HTTP requests to the API.

- `test_historical_data.py`: Tests for the historical data API endpoints

### `/tests/e2e`

End-to-end tests focus on testing the complete system flow through the API. These tests verify that all components work together correctly in real-world scenarios.

- `test_data_flow_api.py`: Tests the core data flow scenario (查询不存在的数据 -> 从AKShare获取 -> 保存到数据库和缓存)
  - Verifies that the API can handle requests for stock data
  - Checks if the caching mechanism is working by comparing query times
  - Validates the complete flow from user request to data retrieval

### Root Tests

The following tests are in the root of the tests directory:

- `test_akshare_adapter_fix.py`: Tests for the AKShare adapter
- `test_api.py`: Basic API tests
- `test_assets_api.py`: Tests for the assets API
- `test_cache.py`: Tests for the cache system
- `test_database.py`: Tests for the database operations
- `test_data_import.py`: Tests for the data import functionality
- `test_downloader.py`: Tests for the data downloader
- `test_mcp_api.py`: Tests for the MCP API
- `test_mcp_cache.py`: Tests for the MCP cache
- `test_reservoir_cache.py`: Tests for the reservoir cache system

## Running Tests

### Prerequisites

Before running tests, make sure you have:

1. Installed all dependencies: `pip install -r requirements.txt`
2. Set up the development environment: `python setup_dev_env.py`

### Running Tests with Database Setup

To run tests with proper database setup, use the provided scripts:

```bash
# Run specific tests that are known to work with our setup
python run_specific_tests.py

# Run all tests (some may fail due to database setup issues)
python run_tests.py

# Run a specific test file with proper setup
python run_tests.py tests/test_assets_api.py
```

### Running End-to-End Tests

End-to-end tests require the API server to be running. Use the dedicated script:

```bash
# Run all end-to-end tests (will start the API server if needed)
python run_e2e_tests.py
```

This script will:
1. Check if the API server is running
2. If not, ask if you want to start it
3. Run all end-to-end tests
4. Stop the API server if it was started by the script

Alternatively, you can:
1. Start the API server manually: `python -m src.api.main`
2. Run the tests: `python -m pytest tests/e2e/test_data_flow_api.py -v`
3. Or run a specific test directly: `python -m tests.e2e.test_data_flow_api`

#### Troubleshooting End-to-End Tests

If end-to-end tests fail, check the following:

1. Make sure the API server is running and accessible at http://localhost:8000
2. Check that the API endpoints being tested actually exist
3. Verify that the test parameters (symbol, dates) are valid
4. Look for detailed error messages in the test output

### Running Tests Directly with pytest

To run tests directly with pytest (may have database setup issues):

```bash
# Run all tests
python -m pytest

# Run a specific test file
python -m pytest tests/unit/test_cache_engine.py

# Run tests with a specific marker
python -m pytest -m "unit"

# Skip end-to-end tests
python -m pytest -k "not e2e"
```

### Test Database Setup

The test database is initialized with test data in `tests/init_test_db.py`. This script:

1. Creates a SQLite database at `database/test_db.db`
2. Creates all required tables
3. Populates the database with test data

## Test-Driven Development Process

We follow a test-driven development (TDD) process in this project:

1. **Write Tests First**: Before implementing a feature, write tests that define the expected behavior
2. **Run Tests to See Them Fail**: Verify that the tests fail as expected
3. **Implement the Feature**: Write the minimum code needed to make the tests pass
4. **Run Tests Again**: Verify that all tests now pass
5. **Refactor**: Clean up the code while ensuring tests continue to pass
6. **Repeat**: Continue this cycle for each new feature or bug fix

### Continuous Integration

Tests are automatically run on GitHub Actions when code is pushed to the repository. The CI workflow:

1. Sets up the Python environment
2. Installs dependencies
3. Initializes the database
4. Runs all tests
5. Reports test coverage

### Troubleshooting Test Failures

If you encounter test failures:

1. **Database Issues**: Make sure the database is properly initialized using `run_tests.py` or `run_specific_tests.py`
2. **Dependency Issues**: Ensure all dependencies are installed and up to date
3. **Test Isolation**: Check if tests are properly isolated and don't depend on the state of other tests
4. **Test Data**: Verify that test data is properly set up in `tests/init_test_db.py`
5. **Test Fixtures**: Make sure you're using the correct test fixtures from `tests/conftest.py`

## Test Organization Guidelines

1. **Unit Tests**: Place in `/tests/unit/`
2. **Integration Tests**: Place in `/tests/integration/`
3. **API Tests**: Place in `/tests/api/`
4. **End-to-End Tests**: Place in `/tests/e2e/`
5. **Test Naming**: Use `test_` prefix for all test files and test functions
6. **Test Independence**: Each test should be independent and not rely on the state from other tests
7. **Test Coverage**: Aim for high test coverage, especially for critical components
8. **Test Documentation**: Document the purpose of each test and any special setup required

## Test Types and When to Use Them

### Test Pyramid

We follow the test pyramid approach, with more unit tests than integration tests, and more integration tests than end-to-end tests:

```
    /\
   /  \
  /E2E \
 /------\
/  API   \
/----------\
/ Integration\
/--------------\
/     Unit      \
------------------
```

### When to Use Each Test Type

1. **Unit Tests**:
   - Use for testing individual components in isolation
   - Should be fast and not depend on external services
   - Focus on testing business logic and edge cases
   - Examples: Testing CacheEngine, FreshnessTracker, AKShareAdapter in isolation

2. **Integration Tests**:
   - Use for testing how components work together
   - May involve multiple components but not the entire system
   - Focus on testing component interactions and data flow
   - Examples: Testing CacheEngine with FreshnessTracker, AKShareAdapter with CacheEngine

3. **API Tests**:
   - Use for testing API endpoints
   - Verify that the API behaves as expected
   - Focus on request/response validation, error handling, and API contracts
   - Examples: Testing /api/v1/prices/symbol/{symbol} endpoint

4. **End-to-End Tests**:
   - Use for testing complete system flows through the API
   - Verify that all components work together correctly in real-world scenarios
   - Focus on user journeys and business scenarios
   - Examples: Testing the core data flow scenario (查询不存在的数据 -> 从AKShare获取 -> 保存到数据库和缓存)

### Multi-Level Testing for Core Scenarios

For the core data flow scenario (查询不存在的数据 -> 从AKShare获取 -> 保存到数据库和缓存), we have tests at multiple levels:
- **Unit tests** for individual components (AKShareAdapter, CacheEngine)
- **Integration tests** for component interactions (AKShareAdapter with CacheEngine)
- **API tests** for the endpoints that expose this functionality
- **End-to-end tests** for the complete flow through the API

This multi-level approach ensures that we catch issues at the appropriate level, making debugging easier and tests more reliable.

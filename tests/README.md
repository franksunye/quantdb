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

### Running Tests Directly with pytest

To run tests directly with pytest (may have database setup issues):

```bash
# Run all tests
python -m pytest

# Run a specific test file
python -m pytest tests/unit/test_cache_engine.py

# Run tests with a specific marker
python -m pytest -m "unit"
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
4. **Test Naming**: Use `test_` prefix for all test files and test functions
5. **Test Independence**: Each test should be independent and not rely on the state from other tests
6. **Test Coverage**: Aim for high test coverage, especially for critical components
7. **Test Documentation**: Document the purpose of each test and any special setup required

# QuantDB Testing Guide

This document provides comprehensive guidelines for testing in the QuantDB project.

## Table of Contents

1. [Test-Driven Development Process](#test-driven-development-process)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [Continuous Integration](#continuous-integration)
7. [Pre-commit Hooks](#pre-commit-hooks)
8. [Troubleshooting](#troubleshooting)
9. [Real HTTP API Testing](#real-http-api-testing)

## Test-Driven Development Process

We follow a test-driven development (TDD) process in this project:

1. **Write Tests First**: Before implementing a feature, write tests that define the expected behavior
2. **Run Tests to See Them Fail**: Verify that the tests fail as expected
3. **Implement the Feature**: Write the minimum code needed to make the tests pass
4. **Run Tests Again**: Verify that all tests now pass
5. **Refactor**: Clean up the code while ensuring tests continue to pass
6. **Repeat**: Continue this cycle for each new feature or bug fix

## Test Organization

Tests are organized into the following directories:

- `tests/`: Root directory for all tests
  - `tests/unit/`: Unit tests for individual components
  - `tests/integration/`: Integration tests for multiple components
  - `tests/api/`: Tests for API endpoints

### Test Types

1. **Unit Tests**: Test individual functions or classes in isolation
2. **Integration Tests**: Test how multiple components work together
3. **API Tests**: Test API endpoints using FastAPI's TestClient
4. **End-to-End Tests**: Test the entire application from the user's perspective
   - **TestClient E2E Tests**: Use FastAPI's TestClient to simulate HTTP requests
   - **Real HTTP E2E Tests**: Use actual HTTP requests to a running server

## Running Tests

### Prerequisites

Before running tests, make sure you have:

1. Installed all dependencies: `pip install -r requirements.txt`
2. Set up the development environment: `python setup_dev_env.py`

### Test Runner Scripts

We provide several scripts to run tests with proper setup:

#### Run Specific Tests

```bash
python run_specific_tests.py
```

This script runs tests that are known to work with our setup, including:
- API tests
- Unit tests
- Integration tests

#### Run a Single Test File

```bash
python run_test.py tests/test_assets_api.py
```

Options:
- `-v`: Enable verbose output
- `-c`: Enable coverage reporting

#### Run Tests with Coverage

```bash
python run_coverage.py
```

Options:
- `test_path`: Path to the test file or directory to run
- `-f, --format`: Coverage report format (term, html, xml)
- `-m, --min-coverage`: Minimum coverage threshold
- `--fail-under`: Fail if coverage is under the minimum threshold

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

## Writing Tests

### Test File Naming

- All test files should start with `test_`
- Test files should be named after the module they test
- Example: `test_cache_engine.py` for testing `cache_engine.py`

### Test Function Naming

- All test functions should start with `test_`
- Test function names should clearly describe what is being tested
- Example: `test_get_historical_stock_data_with_dates`

### Test Structure

Each test should follow the Arrange-Act-Assert pattern:

1. **Arrange**: Set up the test data and environment
2. **Act**: Call the function or method being tested
3. **Assert**: Verify the expected outcome

Example:

```python
def test_get_asset_by_id(test_db):
    """Test getting a specific asset by ID"""
    # Arrange - done by the test_db fixture

    # Act
    response = client.get(f"{API_PREFIX}/assets/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["symbol"] == "000001"
    assert response.json()["name"] == "平安银行"
```

### Using Fixtures

Use fixtures to set up common test data and environments:

```python
@pytest.fixture
def mock_cache_components():
    """Create mock cache components for testing."""
    from unittest.mock import MagicMock

    mock_cache_engine = MagicMock(spec=CacheEngine)
    mock_freshness_tracker = MagicMock(spec=FreshnessTracker)

    return {
        "cache_engine": mock_cache_engine,
        "freshness_tracker": mock_freshness_tracker
    }
```

### Mocking

Use mocking to isolate the code being tested:

```python
@pytest.fixture
def mock_akshare_adapter():
    """Mock the AKShareAdapter to return test data"""
    with patch('src.cache.akshare_adapter.AKShareAdapter.get_stock_data') as mock:
        # Configure the mock to return test data
        mock.return_value = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [102.0, 103.0, 104.0],
            'volume': [1000000, 1100000, 1200000],
            'amount': [100000000, 110000000, 120000000]
        })
        yield mock
```

## Test Coverage

We aim for high test coverage, especially for critical components. Use the coverage report to identify areas that need more tests:

```bash
python run_coverage.py
```

This will generate a coverage report in the terminal and an HTML report in the `coverage_reports/html` directory.

### Coverage Targets

- **Critical components**: 90% or higher
- **Core business logic**: 80% or higher
- **Overall project**: 70% or higher

## Continuous Integration

Tests are automatically run on GitHub Actions when code is pushed to the repository. The CI workflow:

1. Sets up the Python environment
2. Installs dependencies
3. Initializes the database
4. Runs linting and formatting checks
5. Runs all tests
6. Reports test coverage

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality before committing:

1. Install pre-commit: `pip install pre-commit`
2. Install the hooks: `pre-commit install`

The pre-commit hooks will:
- Check code formatting
- Run linting
- Run tests

## Troubleshooting

If you encounter issues with tests:

### Database Issues

- Make sure the database is properly initialized using `run_tests.py` or `run_specific_tests.py`
- Check that the database file exists in the `database` directory
- Verify that the database has the expected tables and data

### Test Isolation

- Make sure tests are properly isolated and don't depend on the state of other tests
- Use fixtures to set up and tear down test data
- Avoid modifying global state in tests

### Test Data

- Verify that test data is properly set up in `tests/init_test_db.py`
- Make sure test data is appropriate for the tests being run
- Use mocking to avoid external dependencies

### Test Fixtures

- Make sure you're using the correct test fixtures from `tests/conftest.py`
- Check that fixtures are properly scoped
- Verify that fixtures are properly cleaning up after themselves

## Real HTTP API Testing

### Overview

Real HTTP API testing involves making actual HTTP requests to a running server, rather than using FastAPI's TestClient. This approach provides several advantages:

- Tests the complete deployment stack, including the HTTP server
- Verifies network transport and serialization/deserialization
- Tests middleware and server configurations
- Simulates real-world usage scenarios

### Running Real HTTP API Tests

To run real HTTP API tests:

1. **Start the test server**:

   ```bash
   python start_test_server.py --port 8766
   ```

2. **Run the tests** in a separate terminal:

   ```bash
   python -m unittest tests.e2e.test_stock_data_http_api
   ```

3. **Stop the server** when done by pressing `Ctrl+C` in the server terminal.

### Test Server Script

The `start_test_server.py` script provides:

- Automatic port availability checking
- Server startup verification
- Detailed logging
- API endpoint testing

### Key Test Scenarios

Real HTTP API tests cover several key scenarios:

1. **Empty Database Flow**: Tests data retrieval when the database is empty
2. **Complete Cache Hit Flow**: Tests data retrieval when all data is in the database
3. **Partial Cache Hit Flow**: Tests data retrieval when some data is in the database
4. **Invalid Symbol Handling**: Tests error handling for invalid inputs

### When to Use Real HTTP API Tests

Use real HTTP API tests when:

- Testing the complete system from end to end
- Verifying deployment configurations
- Testing performance under real-world conditions
- Performing regression testing before releases

For more details, see the [End-to-End Testing Guide](../../tests/e2e/README.md).

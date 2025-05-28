# QuantDB Development Environment Setup

This document provides instructions for setting up the QuantDB development environment.

**Last Updated**: 2025-05-28
**Version**: Simplified Architecture (v0.6.0-sqlite)
**Status**: SQLite Development Environment

## Prerequisites

- Python 3.9 or higher
- Git
- pip (Python package manager)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/franksunye/quantdb.git
cd quantdb
```

### 2. Set Up the Environment

Run the setup script to create directories, install dependencies, and initialize the database:

```bash
python setup_dev_env.py
```

Alternatively, you can perform these steps manually:

#### 2.1. Create Directories

```bash
mkdir -p data/raw
mkdir -p data/processed
mkdir -p logs
mkdir -p database
```

#### 2.2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.3. Initialize the Database

```bash
python -m src.scripts.init_db
```

### 3. Environment Variables

Create a `.env` file in the project root with the following variables (or copy from `.env.example`):

```
# Database Configuration
DATABASE_URL=sqlite:///./database/stock_data.db

# API Configuration
API_PREFIX=/api/v1
DEBUG=True
ENVIRONMENT=development

# Security
SECRET_KEY=temporarysecretkey123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/quantdb.log
```

## Running the API

To run the API locally:

```bash
uvicorn src.api.main:app --reload
```

The API will be available at http://localhost:8000, and the documentation at http://localhost:8000/api/v1/docs.

## Running Tests

QuantDB uses a unified test runner for all testing needs:

### Basic Test Commands

```bash
# Run all tests
python scripts/test_runner.py --all

# Run core functionality tests (unit + API)
python scripts/test_runner.py --unit --api

# Run specific test types
python scripts/test_runner.py --unit      # Unit tests only
python scripts/test_runner.py --api       # API tests only
python scripts/test_runner.py --integration # Integration tests only
```

### Advanced Test Options

```bash
# Run tests with coverage report
python scripts/test_runner.py --coverage

# Run performance tests
python scripts/test_runner.py --performance

# Run specific test file
python scripts/test_runner.py --file tests/unit/test_stock_data_service.py

# Verbose output
python scripts/test_runner.py --unit --verbose
```

### Test Results

The test runner provides comprehensive reporting:
- Individual test file results
- Summary statistics
- Coverage reports (when enabled)
- Performance metrics (when enabled)

**Current Test Status**: 80/80 core functionality tests passing (100%)

## Project Structure

```
quantdb/
├── data/                          # Data directory
│   ├── raw/                       # Raw data files
│   └── processed/                 # Processed data files
├── database/                      # Database files
│   └── stock_data.db              # SQLite database
├── docs/                          # Documentation
├── logs/                          # Log files
├── src/                           # Source code
│   ├── api/                       # API modules
│   │   ├── __init__.py
│   │   ├── database.py            # Database connection
│   │   ├── main.py                # FastAPI application
│   │   ├── models.py              # SQLAlchemy models
│   │   └── schemas.py             # Pydantic schemas
│   ├── mcp/                       # MCP protocol modules
│   │   ├── __init__.py
│   │   ├── interpreter.py         # MCP interpreter
│   │   └── schemas.py             # MCP schemas
│   ├── scripts/                   # Utility scripts
│   │   ├── __init__.py
│   │   └── init_db.py             # Database initialization
│   ├── config.py                  # Configuration
│   ├── database.py                # Legacy database module
│   ├── logger.py                  # Logging setup
│   └── ...                        # Other modules
├── tests/                         # Test files
├── .env                           # Environment variables
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore file
├── requirements.txt               # Python dependencies
└── setup_dev_env.py               # Development environment setup
```

## Development Workflow

1. Create a new branch for your feature or bug fix
2. Make your changes
3. Run tests to ensure everything works
4. Commit your changes
5. Push your branch and create a pull request
6. Wait for CI to pass and for code review

## Troubleshooting

### Database Issues

If you encounter database issues, you can reset the database:

```bash
rm database/stock_data.db
python -m src.scripts.init_db
```

### Dependency Issues

If you encounter dependency issues, try updating your dependencies:

```bash
pip install --upgrade -r requirements.txt
```

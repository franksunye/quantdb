# QuantDB API Service

FastAPI-based API service for QuantDB financial data platform.

## Features

- RESTful API for stock data and asset information
- Built on QuantDB core business logic
- Comprehensive error handling and logging
- OpenAPI/Swagger documentation
- Dependency injection for services

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload

# Or run directly
python main.py
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Endpoints

- `/health` - Health check
- `/api/v1/assets/` - Asset information
- `/api/v1/stocks/` - Stock data
- `/api/v1/cache/` - Cache management
- `/api/v1/batch/` - Batch operations

## Architecture

This API service uses the QuantDB core business logic layer:

- `core.models` - Data models
- `core.services` - Business services
- `core.database` - Database connections
- `core.cache` - Caching layer

## Development

```bash
# Run tests
pytest

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

# src/api/openapi/openapi_utils.py
"""
OpenAPI utilities for the QuantDB API.

This module provides utilities for integrating OpenAPI documentation with the FastAPI application.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.utils.logger import logger


def get_openapi_schema() -> Dict[str, Any]:
    """
    Get the OpenAPI schema from the JSON file.

    Returns:
        Dict[str, Any]: The OpenAPI schema.
    """
    openapi_path = Path(__file__).parent / "openapi.json"
    try:
        with open(openapi_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading OpenAPI schema: {e}")
        return {}


def setup_openapi(app: FastAPI) -> None:
    """
    Set up OpenAPI documentation for the FastAPI application.

    Args:
        app: The FastAPI application.
    """

    # Override the default OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        # Try to load from file first
        schema = get_openapi_schema()
        if schema:
            app.openapi_schema = schema
            return app.openapi_schema

        # Fall back to auto-generated schema
        openapi_schema = get_openapi(
            title="QuantDB API",
            version="0.5.0",
            description="API for accessing financial data from QuantDB",
            routes=app.routes,
        )

        # Customize the schema
        openapi_schema["info"]["contact"] = {
            "name": "QuantDB Support",
            "email": "support@quantdb.example.com",
        }
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    # Set the custom OpenAPI function
    app.openapi = custom_openapi

    # Add a route to serve the OpenAPI schema directly
    @app.get("/api/v2/openapi.json", include_in_schema=False)
    async def get_openapi_endpoint():
        return JSONResponse(app.openapi())

    logger.info("OpenAPI documentation set up successfully")


def setup_swagger_ui(app: FastAPI) -> None:
    """
    Set up Swagger UI for the FastAPI application.

    Args:
        app: The FastAPI application.
    """
    # Create a directory for Swagger UI if it doesn't exist
    swagger_dir = Path(__file__).parent / "swagger-ui"
    os.makedirs(swagger_dir, exist_ok=True)

    # Create a simple HTML file for Swagger UI
    swagger_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>QuantDB API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.5.0/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.5.0/swagger-ui-bundle.js" charset="UTF-8"> </script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: "/api/v2/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    docExpansion: "list",
                    defaultModelsExpandDepth: 1,
                    defaultModelExpandDepth: 1,
                    displayRequestDuration: true,
                }})
                window.ui = ui
            }}
        </script>
    </body>
    </html>
    """

    with open(swagger_dir / "index.html", "w") as f:
        f.write(swagger_html)

    # Mount the Swagger UI directory
    app.mount(
        "/api/v2/docs",
        StaticFiles(directory=str(swagger_dir), html=True),
        name="swagger_ui",
    )

    logger.info("Swagger UI set up successfully")

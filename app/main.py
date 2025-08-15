from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.db.database import _db
from app.routers import data, metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database connection handling."""
    # Connect to database on startup
    await _db.connect()
    yield
    # Disconnect from database on shutdown
    await _db.disconnect()


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION
    + f"""

# User Guide

The Open Enzyme Database API provides programmatic access to the same rich datasets available through the
[Open Enzyme Database user interface](https://openenzymedb.platform.moleculemaker.org).

This page serves as the API documentation, detailing available endpoints, request parameters,
response formats, and example usage. There are also interactive features to test endpoints directly
from your browser.

## Endpoint Documentation, Python Examples, and Interactive Testing

Below you will find a list of available endpoints. Each endpoint appears as a colored box with a title and brief
description. You can click on any endpoint to expand it and see more details, including:
- **Description**: A brief overview of the endpoint's purpose.
- **Example Usage**: Sample code snippets in Python demonstrating how to call the endpoint and handle the response.
- **Parameters**: Required and optional parameters for the endpoint.
- **Response Format**: The structure of the data returned by the endpoint.
- **Try it out**: An interactive feature that allows you to test the endpoint directly from this page.

### Technical Note: Automatic Pagination

When a query would return more than {settings.AUTO_PAGINATION_THRESHOLD} records and no explicit limit is
provided, the API will automatically paginate results to return {settings.AUTO_PAGINATION_THRESHOLD} records
at a time. The response will include pagination metadata with links to navigate
to next and previous pages.

## Support

If you have any questions, issues, or feedback regarding the API, please reach out to us via email at <openenzymedb-feedback@moleculemaker.org>.

""",
    version=settings.VERSION,
    lifespan=lifespan,
    # Increase timeout and response size limits
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
    max_age=600,
)

# Add GZip compression middleware to compress large responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routers
app.include_router(metadata.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")

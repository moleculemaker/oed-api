# OED Data API

A FastAPI application providing access to enzyme kinetic data from the OED database.

## Features

- Query enzyme kinetic data with ability to filter on any column
- Query distinct values for each column to assist with query building
- Support for multiple response formats (JSON and CSV)
- Pagination and column selection
- EC number wildcard filtering

## Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/oedb-rde.git
   cd oedb-rde
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your database credentials if needed
   ```

3. Build and start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the API documentation at http://localhost:8000/docs or http://localhost:8000/redoc

## API Documentation

### Endpoints

#### `GET /api/v1/metadata`

Returns distinct values for string columns to aid in filtering.

Query parameters:
- `column`: Column name to get distinct values for

Examples:
- `/api/v1/metadata?column=organism`
- `/api/v1/metadata?column=ec`

#### `GET /api/v1/data`

Main endpoint for querying enzyme kinetic data with filtering capabilities.

Query parameters:
- String filters (case-insensitive, multiple values with OR logic):
  - `ec`: EC number filter with wildcard support (e.g., `1.1.%`)
  - `substrate`, `organism`, `uniprot`, `enzymetype`, etc.
- Numeric range filters:
  - `ph_min`, `ph_max`, `temperature_min`, `temperature_max`, etc.
- Response format and pagination:
  - `format`: Response format (`json` or `csv`)
  - `columns`: Columns to include in the response
  - `limit`: Maximum number of records to return
  - `offset`: Number of records to skip

Examples:
- `/api/v1/data?organism=Homo%20sapiens&organism=Mus%20musculus&temperature_min=25&temperature_max=40`
- `/api/v1/data?ec=1.1.%&format=csv&limit=100`
- `/api/v1/data?columns=ec&columns=substrate&columns=organism&columns=kcat_value`

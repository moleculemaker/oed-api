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

### Code Examples

#### Using the metadata endpoint with `requests`

```python
import requests

# Get distinct organism values to aid in filtering
response = requests.get("http://localhost:8000/api/v1/metadata", params={"column": "organism"})

if response.status_code == 200:
    organism_data = response.json()
    organisms = organism_data["values"]
    print(f"Found {len(organisms)} distinct organism values")
    print("Sample organisms:")
    for organism in organisms[:5]:  # Display first 5 organisms
        print(f"- {organism}")
    # Sample output might include: 
    # - Trichoderma viride
    # - Paenibacillus thiaminolyticus
    # - Naegleria fowleri
    # - Rhodococcus rhodochrous
    # - Echinosophora koreensis
else:
    print(f"Error: {response.status_code} - {response.text}")
```

#### Querying data as JSON with `requests`

```python
import requests

# Query data using filters based on metadata
params = {
    "organism": ["Trichoderma viride", "Salmonella enterica"],  # Multiple values use OR logic
    "temperature_min": 25,
    "temperature_max": 37,
    "limit": 10  # Limit to 10 results
}

response = requests.get("http://localhost:8000/api/v1/data", params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Total matching records: {data['total']}")
    print(f"Returning records: {len(data['data'])}")
    
    # Access the first record
    if data["data"]:
        first_record = data["data"][0]
        print("\nFirst record:")
        print(f"EC number: {first_record['ec']}")
        print(f"Substrate: {first_record['substrate']}")
        print(f"Organism: {first_record['organism']}")
        print(f"kcat value: {first_record['kcat_value']} {first_record.get('kcat_unit', '')}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

#### Downloading data as CSV with `requests`

```python
import requests
import csv
from io import StringIO

# Query parameters
params = {
    "ec": ["1.14.15.16", "5.3.1.9"],  # Find data for specific EC numbers
    "format": "csv",   # Request CSV format
    "columns": ["ec", "substrate", "organism", "kcat_value", "km_value"],  # Only selected columns
    "limit": 20        # Limit to 20 results
}

# Make the request
response = requests.get("http://localhost:8000/api/v1/data", params=params)

if response.status_code == 200:
    # Parse CSV data
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    
    # Save to file
    with open("oed_data_export.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            writer.writerow(row)
    
    print(f"Data saved to oed_data_export.csv")
    
    # Preview the data
    csv_data.seek(0)  # Reset to beginning of stream
    reader = csv.DictReader(csv_data)
    rows = list(reader)
    if rows:
        print("\nSample of downloaded data:")
        for i, row in enumerate(rows[:3]):
            print(f"\nRecord {i+1}:")
            print(f"EC: {row['ec']}")
            print(f"Substrate: {row['substrate']}")
            print(f"Organism: {row['organism']}")
            if 'kcat_value' in row and row['kcat_value']:
                print(f"kcat value: {row['kcat_value']}")
            if 'km_value' in row and row['km_value']:
                print(f"km value: {row['km_value']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

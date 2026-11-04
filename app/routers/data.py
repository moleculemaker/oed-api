import csv
from contextlib import aclosing
from tempfile import SpooledTemporaryFile
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.background import BackgroundTask

from app.core.config import settings
from app.db.database import Database, get_db
from app.db.queries import get_filtered_data, get_total_count, iter_filtered_data
from app.models.query_params import OEDDataQueryParams, ResponseFormat

# Largest value Postgres accepts for LIMIT and OFFSET
MAX_BIGINT = 2**63 - 1

# Most records one /data response may contain, as an explicit limit or a whole CSV
MAX_DATA_LIMIT = 100_000

# CSV output stays in memory up to this size, then spills to a temp file on disk
CSV_SPOOL_MAX_MEMORY = 8 * 1024 * 1024


async def write_csv(
    rows: AsyncIterator[Dict[str, Any]],
    fieldnames: Optional[List[str]],
    max_rows: Optional[int] = None,
) -> SpooledTemporaryFile:
    """Write rows as CSV to a spooled temp file, rewound for reading.

    The columns are fieldnames, or the first row's keys if fieldnames is None. The whole
    result is written before the response starts, so the DB connection is released at
    the speed of the DB, not the speed of the client reading the response. Raises a 400
    if rows has more than max_rows rows.
    """
    output = SpooledTemporaryFile(max_size=CSV_SPOOL_MAX_MEMORY, mode="w+", newline="")
    try:
        writer = None
        if fieldnames:
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
        # aclosing releases the DB connection now if we stop early, not at garbage collection
        async with aclosing(rows):
            count = 0
            async for row in rows:
                count += 1
                if max_rows is not None and count > max_rows:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Query matches more than {max_rows} records, the most a CSV "
                        "response can contain. Narrow the filters, or page with limit and offset.",
                    )
                if writer is None:
                    writer = csv.DictWriter(output, fieldnames=list(row.keys()), extrasaction="ignore")
                    writer.writeheader()
                writer.writerow(row)
    except BaseException:
        output.close()
        raise
    output.seek(0)
    return output


def read_chunks(file: SpooledTemporaryFile, size: int = 64 * 1024) -> Iterator[str]:
    """Read a file in chunks."""
    while chunk := file.read(size):
        yield chunk

router = APIRouter(tags=["Data"])


def parse_query_params(
    # String filters
    ec: Optional[List[str]] = Query(
        None,
        description="The Enzyme Commission Number filter with wildcard support (e.g., '1.1.%'), describing the type of reaction that is catalyzed by this enzyme.",
    ),
    substrate: Optional[List[str]] = Query(
        None,
        description="The substrate (chemical compound) that is one of the reactants of the enzymatic reaction in question",
    ),
    organism: Optional[List[str]] = Query(
        None,
        description="The organism (e.g. human, horse) in which the data for the enzymatic reaction was measured",
    ),
    uniprot: Optional[List[str]] = Query(
        None,
        description="The unique accession number/identifier from the Uniprot database for the enzyme catalyzing the reaction",
    ),
    enzymetype: Optional[List[str]] = Query(
        None,
        description='Whether the enzyme catalyzing the reaction is "wild-type" (unmutated) or a mutant enzyme',
    ),
    smiles: Optional[List[str]] = Query(
        None, description="SMILES representation of the substrate chemical structure"
    ),
    # Response format and pagination
    format: ResponseFormat = Query(
        default=ResponseFormat.JSON, description="Response format (json or csv)"
    ),
    columns: Optional[List[str]] = Query(
        None, description="Columns to include in the response"
    ),
    limit: Optional[int] = Query(
        None, ge=1, le=MAX_DATA_LIMIT,
        description="Maximum number of records to return "
        f"(at most {settings.AUTO_PAGINATION_THRESHOLD} for JSON, {MAX_DATA_LIMIT} for CSV)",
    ),
    offset: Optional[int] = Query(
        0, ge=0, le=MAX_BIGINT, description="Number of records to skip"
    ),
) -> OEDDataQueryParams:
    """Parse and validate query parameters."""
    # JSON is paginated, so a JSON page is never larger than the default page size.
    # Shaped like the le= error on limit, so both caps fail the same way.
    max_json_limit = settings.AUTO_PAGINATION_THRESHOLD
    if format == ResponseFormat.JSON and limit is not None and limit > max_json_limit:
        raise RequestValidationError([{
            "type": "less_than_equal",
            "loc": ("query", "limit"),
            "msg": f"Input should be less than or equal to {max_json_limit} for JSON responses; "
            "page with offset, or use format=csv",
            "input": str(limit),
            "ctx": {"le": max_json_limit},
        }])

    try:
        # Validate format
        if format not in [fmt for fmt in ResponseFormat]:
            format = ResponseFormat.JSON

        return OEDDataQueryParams(
            ec=ec,
            substrate=substrate,
            organism=organism,
            uniprot=uniprot,
            enzymetype=enzymetype,
            smiles=smiles,
            format=format,
            columns=columns,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error parsing query parameters: {e}")
        raise HTTPException(
            status_code=400, detail=f"Invalid query parameters: {str(e)}"
        )


@router.get("/data", summary="Get enzyme kinetic data")
async def get_data(
    params: OEDDataQueryParams = Depends(parse_query_params),
    db: Database = Depends(get_db),
    request: Request = None,
) -> Any:
    r"""
Get enzyme kinetic data with filtering options.

This endpoint allows querying the Open Enzyme Database with various filters.

All filters on the same column are combined with OR logic, while filters on
different columns are combined with AND logic.

The response format can be either JSON (default) or CSV.

JSON results are automatically paginated when they exceed the configured threshold, unless
an explicit limit is provided; an explicit JSON limit can be at most the threshold. CSV
results are not paginated: without an explicit limit, every matching record is returned,
up to 100,000, and a query matching more gets a 400.

### URL examples

- /api/v1/data?organism=Homo%20sapiens&organism=Mus%20musculus

- /api/v1/data?ec=1.1.%&format=csv&limit=100

- /api/v1/data?columns=ec&columns=substrate&columns=organism

### Python example retrieving JSON data

```python
import requests

# Query data using filters based on metadata
params = {
    "organism": ["Trichoderma viride", "Salmonella enterica"],  # Multiple values use OR logic
    "temperature_min": 25,
    "temperature_max": 37,
    "limit": 10  # Limit to 10 results
}

response = requests.get("https://openenzymedb-api.platform.moleculemaker.org/api/v1/data", params=params)

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

### Python example retrieving CSV data

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
response = requests.get("https://openenzymedb-api.platform.moleculemaker.org/api/v1/data", params=params)

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
    """

    try:
        # CSV is not paginated: without an explicit limit, return every match up to the cap
        if params.format == ResponseFormat.CSV:
            if params.limit is None:
                # Fetch one row past the cap, so a result that is too large is detected
                # while writing instead of silently cut off
                rows = iter_filtered_data(db, params.model_copy(update={"limit": MAX_DATA_LIMIT + 1}))
                csv_file = await write_csv(rows, params.columns, max_rows=MAX_DATA_LIMIT)
            else:
                csv_file = await write_csv(iter_filtered_data(db, params), params.columns)
            return StreamingResponse(
                read_chunks(csv_file),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=oed_data.csv"},
                # Runs after the response ends, including when the client disconnects
                background=BackgroundTask(csv_file.close),
            )

        # Get total count for the query (without pagination)
        total_count = await get_total_count(db, params)

        # Apply automatic pagination if results exceed threshold and no explicit limit,
        # or one equal to it, was provided. A larger one was rejected when parsing.
        # Equal counts because the `next` links below carry limit=threshold, and those
        # pages need links of their own.
        if total_count > settings.AUTO_PAGINATION_THRESHOLD and (
            params.limit is None or params.limit >= settings.AUTO_PAGINATION_THRESHOLD
        ):
            params.auto_paginated = True
            params.limit = settings.AUTO_PAGINATION_THRESHOLD
            logger.info(
                f"Auto-pagination applied. Results limited to {params.limit} records."
            )

        # Get data from database (now with potential auto-pagination applied)
        data = await get_filtered_data(db, params)

        # Pagination links
        next_url = None
        previous_url = None
        if params.auto_paginated and request:
            base_url = str(request.url).split("?")[0]

            # Prepare query parameters for pagination links
            # For Pydantic v2 compatibility
            query_params = {
                k: v
                for k, v in params.model_dump().items()
                if k not in ["auto_paginated", "offset", "limit"]
                and v is not None
            }

            current_offset = params.offset or 0
            current_limit = params.limit or total_count

            # Calculate next page link if there are more records
            if current_offset + current_limit < total_count:
                next_params = {
                    **query_params,
                    "offset": current_offset + current_limit,
                    "limit": current_limit,
                }
                next_url = f"{base_url}?{urlencode(next_params, doseq=True)}"

            # Calculate previous page link if not on first page. Past the end, go
            # back to the last `limit` records instead of another empty page. That
            # isn't necessarily a page boundary: 25 records in pages of 10 gives 15.
            if current_offset > 0:
                prev_params = {
                    **query_params,
                    "offset": max(
                        0, min(current_offset - current_limit, total_count - current_limit)
                    ),
                    "limit": current_limit,
                }
                previous_url = f"{base_url}?{urlencode(prev_params, doseq=True)}"

        # JSON response with enhanced pagination info
        response = {
            "total": total_count,
            "offset": params.offset,
            "limit": params.limit if params.limit is not None else total_count,
            "data": data,
        }

        if params.auto_paginated:
            # Add flag indicating automatic pagination was applied
            response["auto_paginated"] = True
            if next_url:
                response["next"] = next_url
            if previous_url:
                response["previous"] = previous_url

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

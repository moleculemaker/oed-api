import csv
from io import StringIO
from typing import Any, List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from app.core.config import settings
from app.db.database import Database, get_db
from app.db.queries import get_filtered_data, get_total_count
from app.models.query_params import OEDDataQueryParams, ResponseFormat

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
        None, description="Maximum number of records to return"
    ),
    offset: Optional[int] = Query(0, description="Number of records to skip"),
) -> OEDDataQueryParams:
    """Parse and validate query parameters."""
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
    """
    Get enzyme kinetic data with filtering options.

    This endpoint allows querying the OED database with various filters.

    All filters on the same column are combined with OR logic, while filters on
    different columns are combined with AND logic.

    The response format can be either JSON (default) or CSV.

    Results are automatically paginated when they exceed the configured threshold
    (default: configurable via AUTO_PAGINATION_THRESHOLD in config.Settings), unless
    an explicit limit is provided.

    Example queries:

    - /api/v1/data?organism=Homo%20sapiens&organism=Mus%20musculus

    - /api/v1/data?ec=1.1.%&format=csv&limit=100

    - /api/v1/data?columns=ec&columns=substrate&columns=organism
    """

    try:
        # Get total count for the query (without pagination)
        total_count = await get_total_count(db, params)

        # Apply automatic pagination if results exceed threshold and no explicit limit provided
        if total_count > settings.AUTO_PAGINATION_THRESHOLD and params.limit is None:
            params.auto_paginated = True
            params.limit = settings.AUTO_PAGINATION_THRESHOLD
            logger.info(
                f"Auto-pagination applied. Results limited to {params.limit} records."
            )

        # Get data from database (now with potential auto-pagination applied)
        data = await get_filtered_data(db, params)

        # Handle response format
        if params.format == ResponseFormat.CSV:
            # Create CSV response
            output = StringIO()

            # Determine columns to include in CSV
            if params.columns:
                fieldnames = params.columns
            elif data and len(data) > 0:
                fieldnames = list(data[0].keys())
            else:
                fieldnames = []

            # Write CSV
            writer = csv.DictWriter(
                output, fieldnames=fieldnames, extrasaction="ignore"
            )
            writer.writeheader()
            for row in data:
                writer.writerow(row)

            # Return streaming response
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=oed_data.csv"},
            )
        else:
            # JSON response with enhanced pagination info
            response = {
                "total": total_count,
                "offset": params.offset,
                "limit": params.limit if params.limit is not None else total_count,
                "data": data,
            }

            # Add pagination links if automatic pagination was applied
            if params.auto_paginated:
                # Add flag indicating automatic pagination was applied
                response["auto_paginated"] = True

                if request:
                    base_url = str(request.url).split("?")[0]

                    # Prepare query parameters for pagination links
                    # For Pydantic v2 compatibility
                    query_params = {
                        k: v
                        for k, v in params.model_dump().items()
                        if k not in ["auto_paginated", "offset", "limit"]
                        and v is not None
                    }

                    # Set format explicitly if it was provided
                    if params.format != ResponseFormat.JSON:
                        query_params["format"] = params.format

                    # Calculate next page link if there are more records
                    current_offset = params.offset or 0
                    current_limit = params.limit or total_count
                    if current_offset + current_limit < total_count:
                        next_offset = current_offset + current_limit
                        next_params = {
                            **query_params,
                            "offset": next_offset,
                            "limit": current_limit,
                        }
                        response["next"] = (
                            f"{base_url}?{urlencode(next_params, doseq=True)}"
                        )

                    # Calculate previous page link if not on first page
                    current_offset = params.offset or 0
                    current_limit = params.limit or total_count
                    if current_offset > 0:
                        prev_offset = max(0, current_offset - current_limit)
                        prev_params = {
                            **query_params,
                            "offset": prev_offset,
                            "limit": current_limit,
                        }
                        response["previous"] = (
                            f"{base_url}?{urlencode(prev_params, doseq=True)}"
                        )

            return response

    except Exception as e:
        logger.error(f"Error getting data: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

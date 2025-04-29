import csv
from io import StringIO
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

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
    # Numeric range filters
    ph_min: Optional[float] = Query(
        None,
        description="Minimum pH value at which the data for the enzyme catalyzed reaction was collected",
    ),
    ph_max: Optional[float] = Query(
        None,
        description="Maximum pH value at which the data for the enzyme catalyzed reaction was collected",
    ),
    temperature_min: Optional[float] = Query(
        None,
        description="Minimum temperature (in degrees Celsius) at which the data for the enzyme catalyzed reaction was collected",
    ),
    temperature_max: Optional[float] = Query(
        None,
        description="Maximum temperature (in degrees Celsius) at which the data for the enzyme catalyzed reaction was collected",
    ),
    kcat_value_min: Optional[float] = Query(
        None,
        description="Minimum Michaelis-Menten catalytic rate constant (kcat) value",
    ),
    kcat_value_max: Optional[float] = Query(
        None,
        description="Maximum Michaelis-Menten catalytic rate constant (kcat) value",
    ),
    km_value_min: Optional[float] = Query(
        None,
        description="Minimum Michaelis-Menten, Michaelis constant value (in concentration units)",
    ),
    km_value_max: Optional[float] = Query(
        None,
        description="Maximum Michaelis-Menten, Michaelis constant value (in concentration units)",
    ),
    kcatkm_value_min: Optional[float] = Query(
        None,
        description="Minimum Michaelis-Menten catalytic efficiency (also known as specificity constant) value",
    ),
    kcatkm_value_max: Optional[float] = Query(
        None,
        description="Maximum Michaelis-Menten catalytic efficiency (also known as specificity constant) value",
    ),
    kcatkm_threshold_delta_min: Optional[float] = Query(
        None,
        description="Minimum calculated absolute difference between the measured kcatkm_value and the computed value from kcat_value/km_value",
    ),
    kcatkm_threshold_delta_max: Optional[float] = Query(
        None,
        description="Maximum calculated absolute difference between the measured kcatkm_value and the computed value from kcat_value/km_value",
    ),
    # PubMed ID filters
    kcat_pubmedid: Optional[List[float]] = Query(
        None,
        description="The PubMed Identifier for the experimental details from which the kcat data was collected",
    ),
    km_pubmedid: Optional[List[float]] = Query(
        None,
        description="The PubMed Identifier for the experimental details from which the Km data was collected",
    ),
    kcatkm_pubmedid: Optional[List[float]] = Query(
        None,
        description="The PubMed Identifier for the experimental details from which the kcat/Km data was collected",
    ),
    # Response format and pagination
    format: Optional[ResponseFormat] = Query(
        ResponseFormat.JSON.value, description="Response format (json or csv)"
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
        if format not in [fmt.value for fmt in ResponseFormat]:
            format = ResponseFormat.JSON.value

        return OEDDataQueryParams(
            ec=ec,
            substrate=substrate,
            organism=organism,
            uniprot=uniprot,
            enzymetype=enzymetype,
            smiles=smiles,
            ph_min=ph_min,
            ph_max=ph_max,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            kcat_value_min=kcat_value_min,
            kcat_value_max=kcat_value_max,
            km_value_min=km_value_min,
            km_value_max=km_value_max,
            kcatkm_value_min=kcatkm_value_min,
            kcatkm_value_max=kcatkm_value_max,
            kcatkm_threshold_delta_min=kcatkm_threshold_delta_min,
            kcatkm_threshold_delta_max=kcatkm_threshold_delta_max,
            kcat_pubmedid=kcat_pubmedid,
            km_pubmedid=km_pubmedid,
            kcatkm_pubmedid=kcatkm_pubmedid,
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
) -> Any:
    """
    Get enzyme kinetic data with filtering options.

    This endpoint allows querying the OED database with various filters.

    All filters on the same column are combined with OR logic, while filters on
    different columns are combined with AND logic.

    The response format can be either JSON (default) or CSV.

    Example queries:

    - /api/v1/data?organism=Homo%20sapiens&organism=Mus%20musculus&temperature_min=25&temperature_max=40

    - /api/v1/data?ec=1.1.%&format=csv&limit=100

    - /api/v1/data?columns=ec&columns=substrate&columns=organism&columns=kcat_value
    """

    try:
        # Get data from database
        data = await get_filtered_data(db, params)

        # Get total count for the query (without pagination)
        total_count = await get_total_count(db, params)

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
            # JSON response
            return {
                "total": total_count,
                "offset": params.offset,
                "limit": params.limit if params.limit is not None else total_count,
                "data": data,
            }

    except Exception as e:
        logger.error(f"Error getting data: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

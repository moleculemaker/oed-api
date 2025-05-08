from typing import Any, Dict, List, Tuple

import rich

from app.db.database import Database
from app.models.oed_data import OEDColumn
from app.models.query_params import OEDDataQueryParams


async def get_column_values(db: Database, column: str) -> List[str]:
    """Get distinct values for a column."""

    # Fast API will already have validated that column is in the
    # FilterableColumn enum from app.v1.endpoints.metadata.get_metadata but, in
    # case this is called elsewhere down the road, might as well to validation
    # here too.
    if column not in [column.value for column in OEDColumn]:
        raise ValueError(f"Invalid OED column: {column}")

    query = f"""
    SELECT DISTINCT {column}
    FROM oed.oed_data
    WHERE {column} IS NOT NULL
    ORDER BY {column}
    """

    records = await db.fetch(query)
    return [record[column] for record in records if record[column]]


async def build_query_conditions(
    params: OEDDataQueryParams,
) -> Tuple[str, Dict[str, Any]]:
    """Build SQL query conditions from query parameters."""
    conditions = []
    query_params = {}
    param_idx = 0

    # Process string filters (case-insensitive exact matches with OR logic within columns)
    string_columns = {
        "ec": params.ec,
        "substrate": params.substrate,
        "organism": params.organism,
        "uniprot": params.uniprot,
        "enzymetype": params.enzymetype,
        "smiles": params.smiles,
    }

    for column, values in string_columns.items():
        if values:
            column_conditions = []

            for value in values:
                param_idx += 1
                param_name = f"param_{param_idx}"

                # Special handling for EC number with wildcard support
                if column == "ec" and "%" in value:
                    column_conditions.append(f"{column} LIKE ${param_idx}")
                else:
                    column_conditions.append(f"LOWER({column}) = LOWER(${param_idx})")

                query_params[param_name] = value

            if column_conditions:
                conditions.append(f"({' OR '.join(column_conditions)})")

    # Process numeric range filters
    range_filters = []  # Removed as requested

    for column, min_val, max_val in range_filters:
        if min_val is not None:
            param_idx += 1
            param_name = f"param_{param_idx}"
            conditions.append(f"{column} >= ${param_idx}")
            query_params[param_name] = min_val

        if max_val is not None:
            param_idx += 1
            param_name = f"param_{param_idx}"
            conditions.append(f"{column} <= ${param_idx}")
            query_params[param_name] = max_val

    # Process PubMed ID filters
    pubmed_filters = []  # Removed as requested

    for column, values in pubmed_filters:
        if values:
            pubmed_conditions = []

            for value in values:
                param_idx += 1
                param_name = f"param_{param_idx}"
                pubmed_conditions.append(f"{column} = ${param_idx}")
                query_params[param_name] = value

            if pubmed_conditions:
                conditions.append(f"({' OR '.join(pubmed_conditions)})")

    # Combine all conditions with AND logic
    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    return where_clause, query_params


async def get_filtered_data(
    db: Database, params: OEDDataQueryParams
) -> List[Dict[str, Any]]:
    """Get filtered data from the database."""
    where_clause, query_params = await build_query_conditions(params)

    # Determine which columns to select, default to all columns
    columns_to_select = "*"
    if params.columns:
        # Validate column names to prevent SQL injection
        # First generate a list from Enum
        oed_columns = [oed_column.value for oed_column in OEDColumn]

        # Now validate column names
        valid_columns = [col for col in params.columns if col in oed_columns]
        if valid_columns:
            columns_to_select = ", ".join(valid_columns)

    # Build the main query
    query = f"""
    SELECT {columns_to_select}
    FROM oed.oed_data
    WHERE {where_clause}
    """

    # Add pagination
    if params.limit is not None:
        query += f" LIMIT {params.limit}"

    if params.offset is not None:
        query += f" OFFSET {params.offset}"

    # Extract query parameters from the dictionary
    query_args = list(query_params.values())

    # Execute the query
    records = await db.fetch(query, *query_args)
    rich.print(f"{records=}")
    return records


async def get_total_count(db: Database, params: OEDDataQueryParams) -> int:
    """Get total count of records matching the filters."""
    where_clause, query_params = await build_query_conditions(params)

    query = f"""
    SELECT COUNT(*) as count
    FROM oed.oed_data
    WHERE {where_clause}
    """

    # Extract query parameters from the dictionary
    query_args = list(query_params.values())

    # Execute the query
    result = await db.fetchval(query, *query_args)
    return result

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    """Enum for response format options."""

    JSON = "json"
    CSV = "csv"


class OEDDataQueryParams(BaseModel):
    """Query parameters for OED data filtering."""

    # Flag for automatic pagination
    auto_paginated: bool = Field(
        False, 
        description="Whether results are automatically paginated"
    )

    # String filters (exact match, case-insensitive, multiple values with OR logic)
    ec: Optional[List[str]] = Field(
        None,
        description="The Enzyme Commission Number filter with wildcard support (e.g., '1.1.%'), describing the type of reaction that is catalyzed by this enzyme.",
    )
    substrate: Optional[List[str]] = Field(
        None,
        description="The substrate (chemical compound) that is one of the reactants of the enzymatic reaction in question",
    )
    organism: Optional[List[str]] = Field(
        None,
        description="The organism (e.g. human, horse) in which the data for the enzymatic reaction was measured",
    )
    uniprot: Optional[List[str]] = Field(
        None,
        description="The unique accession number/identifier from the Uniprot database for the enzyme catalyzing the reaction",
    )
    enzymetype: Optional[List[str]] = Field(
        None,
        description='Whether the enzyme catalyzing the reaction is "wild-type" (unmutated) or a mutant enzyme',
    )
    smiles: Optional[List[str]] = Field(
        None, description="SMILES representation of the substrate chemical structure"
    )

    # Numeric range filters (removed as requested)

    # PubMed ID filters (removed as requested)

    # Response format and pagination
    format: Optional[ResponseFormat] = Field(
        ResponseFormat.JSON, description="Response format (json or csv)"
    )
    columns: Optional[List[str]] = Field(
        None, description="Columns to include in the response"
    )
    limit: Optional[int] = Field(
        None, description="Maximum number of records to return"
    )
    offset: Optional[int] = Field(0, description="Number of records to skip")


class MetadataQueryParams(BaseModel):
    """Query parameters for metadata."""

    column: str = Field(
        ...,
        description="Column name to get distinct values for. Available columns include: ec, substrate, organism, uniprot, enzymetype, smiles.",
    )

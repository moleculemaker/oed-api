from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    """Enum for response format options."""

    JSON = "json"
    CSV = "csv"


class OEDDataQueryParams(BaseModel):
    """Query parameters for OED data filtering."""

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

    # Numeric range filters
    ph_min: Optional[float] = Field(
        None,
        description="Minimum pH value at which the data for the enzyme catalyzed reaction was collected",
    )
    ph_max: Optional[float] = Field(
        None,
        description="Maximum pH value at which the data for the enzyme catalyzed reaction was collected",
    )
    temperature_min: Optional[float] = Field(
        None,
        description="Minimum temperature (in degrees Celsius) at which the data for the enzyme catalyzed reaction was collected",
    )
    temperature_max: Optional[float] = Field(
        None,
        description="Maximum temperature (in degrees Celsius) at which the data for the enzyme catalyzed reaction was collected",
    )
    kcat_value_min: Optional[float] = Field(
        None,
        description="Minimum Michaelis-Menten catalytic rate constant (kcat) value",
    )
    kcat_value_max: Optional[float] = Field(
        None,
        description="Maximum Michaelis-Menten catalytic rate constant (kcat) value",
    )
    km_value_min: Optional[float] = Field(
        None,
        description="Minimum Michaelis-Menten, Michaelis constant value (in concentration units)",
    )
    km_value_max: Optional[float] = Field(
        None,
        description="Maximum Michaelis-Menten, Michaelis constant value (in concentration units)",
    )
    kcatkm_value_min: Optional[float] = Field(
        None,
        description="Minimum Michaelis-Menten catalytic efficiency (also known as specificity constant) value",
    )
    kcatkm_value_max: Optional[float] = Field(
        None,
        description="Maximum Michaelis-Menten catalytic efficiency (also known as specificity constant) value",
    )
    kcatkm_threshold_delta_min: Optional[float] = Field(
        None,
        description="Minimum calculated absolute difference between the measured kcatkm_value and the computed value from kcat_value/km_value",
    )
    kcatkm_threshold_delta_max: Optional[float] = Field(
        None,
        description="Maximum calculated absolute difference between the measured kcatkm_value and the computed value from kcat_value/km_value",
    )

    # PubMed ID filters
    kcat_pubmedid: Optional[List[float]] = Field(
        None,
        description="The PubMed Identifier for the experimental details from which the kcat data was collected",
    )
    km_pubmedid: Optional[List[float]] = Field(
        None,
        description="The PubMed Identifier for the experimental details from which the Km data was collected",
    )
    kcatkm_pubmedid: Optional[List[float]] = Field(
        None,
        description="The PubMed Identifier for the experimental details from which the kcat/Km data was collected",
    )

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
        description="Column name to get distinct values for. Available columns include: ec, substrate, organism, uniprot, enzymetype, kcat_unit, km_unit, kcatkm_unit, smiles.",
    )

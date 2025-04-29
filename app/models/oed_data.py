from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# class OEDFilterableColumn(Enum):
#     ec = "ec"
#     substrate = "substrate"
#     organism = "organism"
#     uniprot = "uniprot"
#     enzymetype = "enzymetype"
#     ph = "ph"
#     temperature = "temperature"
#     smiles = "smiles"
#     kcat_value = "kcat_value"
#     kcat_pubmedid = "kcat_pubmedid"
#     kcat_unit = "kcat_unit"
#     km_value = "km_value"
#     km_pubmedid = "km_pubmedid"
#     km_unit = "km_unit"
#     kcatkm_value = "kcatkm_value"
#     kcatkm_pubmedid = "kcatkm_pubmedid"
#     kcatkm_unit = "kcatkm_unit"
#     kcatkm_threshold_delta = "kcatkm_threshold_delta"


class OEDColumn(Enum):
    ec = "ec"
    substrate = "substrate"
    organism = "organism"
    uniprot = "uniprot"
    enzymetype = "enzymetype"
    ph = "ph"
    temperature = "temperature"
    smiles = "smiles"
    kcat_value = "kcat_value"
    kcat_pubmedid = "kcat_pubmedid"
    kcat_unit = "kcat_unit"
    km_value = "km_value"
    km_pubmedid = "km_pubmedid"
    km_unit = "km_unit"
    kcatkm_value = "kcatkm_value"
    kcatkm_pubmedid = "kcatkm_pubmedid"
    kcatkm_unit = "kcatkm_unit"
    kcatkm_threshold_delta = "kcatkm_threshold_delta"


class OEDDataBase(BaseModel):
    """Base model for OED data."""

    ec: Optional[str] = Field(
        None,
        description="The Enzyme Commission Number, describing the type of reaction that is catalyzed by this enzyme. For examples of the EC Number hierarchy, please see the Open Enzyme Database Home Page, Statistics View.",
    )
    substrate: Optional[str] = Field(
        None,
        description="The substrate (chemical compound) that is one of the reactants of the enzymatic reaction in question",
    )
    organism: Optional[str] = Field(
        None,
        description="The organism (e.g. human, horse) in which the data for the enzymatic reaction was measured",
    )
    uniprot: Optional[str] = Field(
        None,
        description="The unique accession number/identifier from the Uniprot database: https://www.uniprot.org/ for the enzyme catalyzing the reaction in question",
    )
    enzymetype: Optional[str] = Field(
        None,
        description='Whether the enzyme catalyzing the reaction is "wild-type" (unmutated) or a mutant enzyme.',
    )
    ph: Optional[float] = Field(
        None,
        description="The pH at which the data for the enzyme catalyzed reaction was collected.",
    )
    temperature: Optional[float] = Field(
        None,
        description="The temperature (in degrees Celsius) at which the data for the enzyme catalyzed reaction was collected.",
    )
    smiles: Optional[str] = Field(
        None, description="SMILES representation of the substrate chemical structure"
    )
    kcat_value: Optional[float] = Field(
        None,
        description="The Michaelis-Menten catalytic rate constant (kcat) that was measured for the enzymatic reaction.",
    )
    kcat_pubmedid: Optional[float] = Field(
        None,
        description="The PubMed Identifier (https://pubmed.ncbi.nlm.nih.gov/) for the experimental details from which the kcat data was collected.",
    )
    kcat_unit: Optional[str] = Field(
        None, description="The unit of measurement for the kcat value"
    )
    km_value: Optional[float] = Field(
        None,
        description="The Michaelis-Menten, Michaelis constant (in units of concentration - millimolar) for the enzymatic reaction.",
    )
    km_pubmedid: Optional[float] = Field(
        None,
        description="The PubMed Identifier (https://pubmed.ncbi.nlm.nih.gov/) for the experimental details from which the Km data was collected.",
    )
    km_unit: Optional[str] = Field(
        None, description="The unit of measurement for the Km value"
    )
    kcatkm_value: Optional[float] = Field(
        None,
        description="The Michaelis-Menten catalytic efficiency (also known as specificity constant) in units of /second/mM for enzymatic reaction.",
    )
    kcatkm_pubmedid: Optional[float] = Field(
        None,
        description="The PubMed Identifier (https://pubmed.ncbi.nlm.nih.gov/) for the experimental details from which the kcat/Km data was collected.",
    )
    kcatkm_unit: Optional[str] = Field(
        None, description="The unit of measurement for the kcat/Km value"
    )
    kcatkm_threshold_delta: Optional[float] = Field(
        None,
        description="Calculated absolute difference between the measured kcatkm_value and the computed value from kcat_value/km_value",
    )


class OEDColumnValues(BaseModel):
    """Response model for metadata."""

    column: str = Field(
        ..., description="Column name for which distinct values are provided"
    )
    values: List[str] = Field(
        ...,
        description="List of distinct values found in the database for the specified column",
    )

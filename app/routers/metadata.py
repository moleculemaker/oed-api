from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.db.database import Database, get_db
from app.db.queries import get_column_values
from app.models.oed_data import OEDColumn, OEDColumnValues

router = APIRouter(tags=["Metadata"])


@router.get("/metadata", summary="Get metadata for a column")
async def get_metadata(
    column: OEDColumn,
    db: Database = Depends(get_db),
) -> OEDColumnValues:
    r"""
Get distinct values for a specified column.

This endpoint returns a list of all distinct values for a specified column
in the OED data set. This is useful to inspect what values can be used
for a more targeted download.

### URL examples

- /api/v1/metadata?column=organism

- /api/v1/metadata?column=ec

### Python example

```python
import requests

# Get distinct organism values to aid in filtering
response = requests.get("https://fastapi.openenzymedb.mmli1.ncsa.illinois.edu/api/v1/metadata", params={"column": "organism"})

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
    """
    try:
        values = await get_column_values(db, column=column.value)
        return OEDColumnValues(column=column.value, values=values)
    except Exception as e:
        logger.error(f"Error getting metadata: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving metadata: {str(e)}"
        )

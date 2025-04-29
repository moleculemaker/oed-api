import pytest
import rich

from app.db.queries import get_column_values
from app.models.oed_data import OEDColumn


@pytest.mark.asyncio
async def test_metadata_sql(mock_db, sql_capture):
    """Test SQL generation for metadata endpoint."""
    # Test for each filterable column
    for column_enum in OEDColumn:
        column = column_enum.value

        # Clear previous captured queries
        sql_capture.clear()

        # Execute query
        await get_column_values(mock_db, column)
        rich.print(f"column values sql:{sql_capture[0].get('query')}")
        rich.print(f"column values sql:{sql_capture[0].get('args')=}")

        # Verify SQL
        assert len(sql_capture) >= 1
        query_info = sql_capture[0]
        query = query_info["query"]

        # Check SQL structure
        assert f"SELECT DISTINCT {column}" in query
        assert "FROM oed.oed_data" in query
        assert f"WHERE {column} IS NOT NULL" in query
        assert f"ORDER BY {column}" in query


@pytest.mark.asyncio
async def test_invalid_column_raises_error(mock_db):
    """Test that requesting metadata for an invalid column raises an error."""
    with pytest.raises(ValueError):
        await get_column_values(mock_db, "invalid_column")

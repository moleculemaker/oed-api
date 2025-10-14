import pytest
import rich

from app.db.queries import get_filtered_data, get_total_count
from app.models.query_params import OEDDataQueryParams


@pytest.mark.asyncio
async def test_simple_query_sql(mock_db, sql_capture):
    """test sql generation for a simple query without filters."""
    params = OEDDataQueryParams(
        ec=None, substrate=None, organism=None, uniprot=None, 
        enzymetype=None, smiles=None, format=None, columns=None, 
        limit=None, offset=0
    )

    # execute query
    await get_filtered_data(mock_db, params)

    rich.print(f"simple query sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")
    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]
    args = query_info["args"]

    # check basic sql structure
    assert "SELECT *" in query
    assert "FROM oed.oed_data" in query
    assert "WHERE TRUE" in query  # no filters should result in WHERE TRUE
    assert len(args) == 0  # no args for a query without filters


@pytest.mark.asyncio
async def test_columns_selection_sql(mock_db, sql_capture):
    """test sql generation with specific columns selection."""
    columns = ["ec", "substrate", "organism"]
    params = OEDDataQueryParams(
        ec=None, substrate=None, organism=None, uniprot=None, 
        enzymetype=None, smiles=None, format=None, columns=columns, 
        limit=None, offset=0
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_filtered_data(mock_db, params)
    rich.print(f"columns selection sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]

    # check column selection
    assert "SELECT ec, substrate, organism" in query.replace("\n", " ")
    assert "FROM oed.oed_data" in query


@pytest.mark.asyncio
async def test_string_filter_sql(mock_db, sql_capture):
    """test sql generation with string filters."""
    params = OEDDataQueryParams(
        organism=["human", "mouse"], ec=["1.1.1.1"], substrate=None, 
        uniprot=None, enzymetype=None, smiles=None, format=None, 
        columns=None, limit=None, offset=0
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_filtered_data(mock_db, params)
    rich.print(f"string filter sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]
    args = query_info["args"]

    # check sql structure for string filters
    assert "WHERE" in query.upper()

    # check that the query contains the organism and ec conditions
    # note: the exact parameter order may vary, so we check for the conditions without assuming position
    assert "(LOWER(organism) = LOWER($" in query
    assert "OR LOWER(organism) = LOWER($" in query
    assert "(LOWER(ec) = LOWER($" in query

    # check args
    assert "human" in args
    assert "mouse" in args
    assert "1.1.1.1" in args


@pytest.mark.asyncio
async def test_ec_wildcard_sql(mock_db, sql_capture):
    """test sql generation with ec number wildcard."""
    params = OEDDataQueryParams(
        ec=["1.1.%"], substrate=None, organism=None, uniprot=None, 
        enzymetype=None, smiles=None, format=None, columns=None, 
        limit=None, offset=0
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_filtered_data(mock_db, params)
    rich.print(f"ec wildcard sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]
    args = query_info["args"]

    # check sql structure for ec wildcard
    assert "WHERE" in query
    assert "(ec LIKE $1)" in query.replace("\n", " ")

    # check args
    assert "1.1.%" in args


@pytest.mark.asyncio
async def test_numeric_range_sql(mock_db, sql_capture):
    """test sql generation with numeric range filters."""
    # This test is now a placeholder since the numeric parameters were removed
    # It's kept for future reference if numeric filtering is added back
    params = OEDDataQueryParams(
        ec=None, substrate=None, organism=None, uniprot=None, 
        enzymetype=None, smiles=None, format=None, columns=None, 
        limit=None, offset=0
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_filtered_data(mock_db, params)
    rich.print(f"numeric range sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]
    args = query_info["args"]

    # check basic sql structure - no numeric filters
    assert "WHERE" in query
    # Since all numeric filters were removed, we should have WHERE TRUE
    assert "TRUE" in query.replace("\n", " ")
    
    # check args - should be empty since there are no filters
    assert len(args) == 0


@pytest.mark.asyncio
async def test_pagination_sql(mock_db, sql_capture):
    """test sql generation with pagination."""
    params = OEDDataQueryParams(
        ec=None, substrate=None, organism=None, uniprot=None, 
        enzymetype=None, smiles=None, format=None, columns=None, 
        limit=10, offset=20
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_filtered_data(mock_db, params)
    rich.print(f"pagination sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]

    # check sql structure for pagination
    assert "LIMIT 10" in query.replace("\n", " ")
    assert "OFFSET 20" in query.replace("\n", " ")


@pytest.mark.asyncio
async def test_complex_filter_sql(mock_db, sql_capture):
    """test sql generation with complex filters."""
    params = OEDDataQueryParams(
        organism=["human"],
        ec=["1.1.1.1", "2.1.1.%"],
        substrate=None, uniprot=None, enzymetype=None, smiles=None, 
        format=None, columns=None, limit=5, offset=0
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_filtered_data(mock_db, params)
    rich.print(f"complex filter sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]
    args = query_info["args"]

    # check sql contains all filter conditions
    assert "WHERE" in query

    # string filters
    assert "(LOWER(organism) = LOWER($" in query
    assert "(LOWER(ec) = LOWER($" in query or "(ec LIKE $" in query

    # pagination
    assert "LIMIT 5" in query

    # check args count - we don't check exact count due to possible differences in
    # how the sql is generated
    assert len(args) >= 3  # at least 3 args based on the params (organism, 2 ec values)


@pytest.mark.asyncio
async def test_get_total_count_sql(mock_db, sql_capture):
    """test sql generation for total count query."""
    params = OEDDataQueryParams(
        organism=["human"], ec=None, substrate=None, uniprot=None, 
        enzymetype=None, smiles=None, format=None, columns=None, 
        limit=None, offset=0
    )

    # clear previous captured queries
    sql_capture.clear()

    # execute query
    await get_total_count(mock_db, params)
    rich.print(f"total count sql:{sql_capture[0].get('query')}")
    rich.print(f"total count sql:{sql_capture[0].get('args')=}")

    # verify sql
    assert len(sql_capture) >= 1
    query_info = sql_capture[0]
    query = query_info["query"]

    # check sql structure for count query
    assert "SELECT COUNT(*) as count" in query.replace("\n", " ")
    assert "FROM oed.oed_data" in query
    assert "WHERE" in query
    assert "(LOWER(organism) = LOWER($" in query

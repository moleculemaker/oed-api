import pytest
import rich

from app.db.queries import get_filtered_data, get_total_count
from app.models.query_params import OEDDataQueryParams


@pytest.mark.asyncio
async def test_simple_query_sql(mock_db, sql_capture):
    """test sql generation for a simple query without filters."""
    params = OEDDataQueryParams()

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
    params = OEDDataQueryParams(columns=columns)

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
    params = OEDDataQueryParams(organism=["human", "mouse"], ec=["1.1.1.1"])

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
    params = OEDDataQueryParams(ec=["1.1.%"])

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
    params = OEDDataQueryParams(
        ph_min=6.0, ph_max=8.0, temperature_min=25.0, temperature_max=37.0
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

    # check sql structure for numeric range filters
    assert "WHERE" in query
    assert "ph >= $1" in query.replace("\n", " ")
    assert "ph <= $2" in query.replace("\n", " ")
    assert "temperature >= $3" in query.replace("\n", " ")
    assert "temperature <= $4" in query.replace("\n", " ")

    # check args
    assert 6.0 in args
    assert 8.0 in args
    assert 25.0 in args
    assert 37.0 in args


@pytest.mark.asyncio
async def test_pagination_sql(mock_db, sql_capture):
    """test sql generation with pagination."""
    params = OEDDataQueryParams(limit=10, offset=20)

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
        ph_min=6.5,
        ph_max=7.5,
        temperature_min=30.0,
        kcat_value_min=1.0,
        limit=5,
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

    # numeric range filters
    assert "ph >= $" in query
    assert "ph <= $" in query
    assert "temperature >= $" in query
    assert "kcat_value >= $" in query

    # pagination
    assert "LIMIT 5" in query

    # check args count - we don't check exact count due to possible differences in
    # how the sql is generated
    assert len(args) >= 6  # at least 6 args based on the params


@pytest.mark.asyncio
async def test_get_total_count_sql(mock_db, sql_capture):
    """test sql generation for total count query."""
    params = OEDDataQueryParams(organism=["human"])

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

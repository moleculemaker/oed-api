import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "mock_db",
    [
        # Customize the mock database to return sample data for tests
        {
            "fetch": lambda self, query, *args, **kwargs: [
                {"ec": "1.1.1.1", "substrate": "Test", "organism": "Human"}
            ],
            "fetchval": lambda self, query, *args, **kwargs: 1,
        }
    ],
    indirect=True,
)
def test_data_endpoint_basic(test_client: TestClient, sql_capture):
    """Test that the data endpoint works with basic parameters."""
    # Clear previous captured queries
    sql_capture.clear()

    # Make API request
    response = test_client.get("/api/v1/data")

    # Verify response
    assert response.status_code == 200
    assert "data" in response.json()
    assert "total" in response.json()

    # Verify SQL was captured
    assert len(sql_capture) >= 1  # Should capture at least the data query


@pytest.mark.parametrize(
    "mock_db",
    [
        # Customize the mock database to return sample data for tests
        {
            "fetch": lambda self, query, *args, **kwargs: [
                {
                    "ec": "1.1.1.1",
                    "substrate": "Test",
                    "organism": "Human",
                    "temperature": 30.0,
                }
            ],
            "fetchval": lambda self, query, *args, **kwargs: 1,
        }
    ],
    indirect=True,
)
def test_data_endpoint_with_filters(test_client: TestClient, sql_capture):
    """Test that the data endpoint works with filters."""
    # Clear previous captured queries
    sql_capture.clear()

    # Make API request with filters
    response = test_client.get(
        "/api/v1/data",
        params={
            "organism": ["Human"],
            "limit": 10,
        },
    )

    # Verify response
    assert response.status_code == 200
    assert "data" in response.json()
    assert "total" in response.json()
    assert "limit" in response.json()
    assert response.json()["limit"] == 10

    # Verify SQL was captured
    assert len(sql_capture) >= 2  # Should capture both data and count queries

    # Check if SQL contains the filters
    data_query = None
    count_query = None

    for query_info in sql_capture:
        query = query_info["query"]
        if "COUNT(*)" in query:
            count_query = query
        else:
            data_query = query

    assert data_query is not None
    assert count_query is not None

    # Verify filters in SQL
    for query in [data_query, count_query]:
        assert "LOWER(organism) = LOWER($" in query

    # Verify pagination in data query
    assert "LIMIT 10" in data_query


@pytest.mark.parametrize(
    "mock_db",
    [
        # Customize the mock database to return sample data for tests
        {
            "fetch": lambda self, query, *args, **kwargs: [
                {"ec": "1.1.1.1", "substrate": "Test", "organism": "Human"}
            ],
            "fetchval": lambda self, query, *args, **kwargs: 1,
        }
    ],
    indirect=True,
)
def test_data_endpoint_with_column_selection(test_client: TestClient, sql_capture):
    """Test that the data endpoint respects column selection."""
    # Clear previous captured queries
    sql_capture.clear()

    # Make API request with column selection
    response = test_client.get(
        "/api/v1/data", params={"columns": ["ec", "substrate", "organism"], "limit": 5}
    )

    # Verify response
    assert response.status_code == 200
    assert "data" in response.json()

    # Check if data has only the requested columns
    if response.json()["data"]:
        data_item = response.json()["data"][0]
        assert set(data_item.keys()).issubset({"ec", "substrate", "organism"})

    # Verify SQL was captured
    assert len(sql_capture) >= 1

    # Find the data query
    data_query = None
    for query_info in sql_capture:
        query = query_info["query"]
        if "COUNT(*)" not in query:
            data_query = query
            break

    assert data_query is not None
    assert "SELECT ec, substrate, organism" in data_query.replace("\n", " ")


@pytest.mark.parametrize(
    "mock_db",
    [
        # Customize the mock database to return sample data for tests
        {
            "fetch": lambda self, query, *args, **kwargs: [
                {"ec": "1.1.1.1", "substrate": "Test", "organism": "Human"}
            ],
            "fetchval": lambda self, query, *args, **kwargs: 1,
        }
    ],
    indirect=True,
)
def test_data_endpoint_with_csv_format(test_client: TestClient, sql_capture):
    """Test that the data endpoint returns CSV format when requested."""
    # Clear previous captured queries
    sql_capture.clear()

    # Make API request with CSV format
    response = test_client.get("/api/v1/data", params={"format": "csv", "limit": 5})

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert (
        response.headers["content-disposition"] == "attachment; filename=oed_data.csv"
    )

    # Verify SQL was captured
    assert len(sql_capture) >= 1


@pytest.mark.parametrize(
    "mock_db",
    [
        # Customize the mock database to return sample data for tests
        {
            "fetch": lambda self, query, *args, **kwargs: [
                {"organism": "Human"},
                {"organism": "Mouse"},
                {"organism": "Rat"},
            ],
            "fetchval": lambda self, query, *args, **kwargs: 3,
        }
    ],
    indirect=True,
)
def test_metadata_endpoint(test_client: TestClient, sql_capture):
    """Test that the metadata endpoint works."""
    # Clear previous captured queries
    sql_capture.clear()

    # Make API request
    response = test_client.get("/api/v1/metadata", params={"column": "organism"})

    # Verify response
    assert response.status_code == 200
    assert "column" in response.json()
    assert "values" in response.json()
    assert response.json()["column"] == "organism"

    # Verify SQL was captured
    assert len(sql_capture) >= 1

    # Check SQL
    query_info = sql_capture[0]
    query = query_info["query"]

    assert "SELECT DISTINCT organism" in query
    assert "FROM oed.oed_data" in query
    assert "WHERE organism IS NOT NULL" in query
    assert "ORDER BY organism" in query


def test_metadata_endpoint_invalid_column(test_client: TestClient):
    """Test that the metadata endpoint rejects invalid columns."""
    # Make API request with invalid column
    response = test_client.get("/api/v1/metadata", params={"column": "invalid_column"})

    # Verify response is an error
    assert response.status_code == 422  # Validation error

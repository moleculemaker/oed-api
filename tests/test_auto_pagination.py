import re

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models.query_params import OEDDataQueryParams


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 100,
            "fetch": lambda self, query, *args: [{"id": i, "ec": f"1.1.1.{i}", "organism": f"Test Organism {i}"} for i in range(10)]
        }
    ], 
    indirect=True
)
async def test_auto_pagination_applied(monkeypatch, test_client, mock_db):
    """Test that automatic pagination is applied when results exceed threshold."""
    # Override the pagination threshold for testing
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)
    
    # Override the pagination threshold for this test
    
    # Make request with no explicit limit
    response = test_client.get("/api/v1/data")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify auto-pagination was applied
    assert data["auto_paginated"] is True
    assert data["limit"] == 10
    assert data["total"] == 100
    assert len(data["data"]) == 10
    assert "next" in data
    assert "previous" not in data  # First page
    
    # Check next link
    assert "offset=10" in data["next"]
    assert "limit=10" in data["next"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 100,
            "fetch": lambda self, query, *args: [{"id": i, "ec": f"1.1.1.{i}", "organism": f"Test Organism {i}"} for i in range(5)]
        }
    ], 
    indirect=True
)
async def test_auto_pagination_not_applied_when_explicit_limit(monkeypatch, test_client, mock_db):
    """Test that auto-pagination is not applied when user provides explicit limit."""
    # Override the pagination threshold for testing
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)
    
    # Override the pagination threshold for this test
    
    # Make request with explicit limit
    response = test_client.get("/api/v1/data?limit=5")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify auto-pagination was not applied
    assert "auto_paginated" not in data
    assert data["limit"] == 5
    assert data["total"] == 100
    assert len(data["data"]) == 5
    assert "next" not in data
    assert "previous" not in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 50,
            "fetch": lambda self, query, *args: [{"id": i, "ec": f"1.1.1.{i}", "organism": f"Test Organism {i}"} for i in range(50)]
        }
    ], 
    indirect=True
)
async def test_auto_pagination_not_needed(monkeypatch, test_client, mock_db):
    """Test that auto-pagination is not applied when results are below threshold."""
    # Override the pagination threshold for testing
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 100)
    
    # Override the pagination threshold for this test
    
    # Make request with no explicit limit
    response = test_client.get("/api/v1/data")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify auto-pagination was not applied
    assert "auto_paginated" not in data
    assert data["limit"] == 50  # Default to total count
    assert data["total"] == 50
    assert len(data["data"]) == 50
    assert "next" not in data
    assert "previous" not in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 25,
            "fetch": lambda self, query, *args: [{"id": i, "ec": f"1.1.1.{i}", "organism": f"Test Organism {i}"} for i in range(10)]
        }
    ], 
    indirect=True
)
async def test_pagination_navigation(monkeypatch, test_client, mock_db):
    """Test that following `next` reaches the last page.

    Every page after the first is requested with an explicit limit equal to the
    threshold, so it must still be treated as paginated and carry its own links."""
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)

    offsets = []
    url = "/api/v1/data"
    while url:
        data = test_client.get(url).json()
        offsets.append(data["offset"])
        url = data.get("next", "").replace("http://testserver", "")

    assert offsets == [0, 10, 20]
    assert "offset=10" in data["previous"]

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 100,
            "fetch": lambda self, query, *args: [{"id": i, "ec": f"1.1.1.{i}", "organism": f"Test Organism {i}"} for i in range(10)]
        }
    ], 
    indirect=True
)
async def test_explicit_limit_above_threshold_is_capped(monkeypatch, test_client, mock_db, sql_capture):
    """Test that an explicit limit larger than the threshold is reduced to the threshold.

    Without the cap, one request can load the whole table into memory."""
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)

    response = test_client.get("/api/v1/data?limit=1000")

    assert response.status_code == 200
    data = response.json()

    # The query itself is limited, not just the response
    data_query = [q["query"] for q in sql_capture if "COUNT(*)" not in q["query"]][0]
    assert re.search(r"LIMIT 10\b", data_query)

    assert data["auto_paginated"] is True
    assert data["limit"] == 10
    assert data["total"] == 100
    assert "offset=10" in data["next"]
    assert "limit=10" in data["next"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 100,
            "fetch": lambda self, query, *args: [{"id": i, "ec": "1.1.1.1", "organism": "Distinctive organism"} for i in range(5)]
        }
    ], 
    indirect=True
)
async def test_results_are_not_printed(test_client, mock_db, capsys):
    """Test that query results are not written to stdout.

    Printing every record of a large result set cost far more memory than the records."""
    response = test_client.get("/api/v1/data?limit=5")

    assert response.status_code == 200
    assert "Distinctive organism" not in capsys.readouterr().out


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db", 
    [
        {
            "fetchval": lambda self, query, *args: 100,
            "fetch": lambda self, query, *args: [{"id": i, "ec": f"1.1.1.{i}", "organism": f"Test Organism {i}"} for i in range(10)]
        }
    ], 
    indirect=True
)
async def test_capped_csv_says_there_is_more(monkeypatch, test_client, mock_db):
    """Test that a CSV response cut off by the cap says so in its headers.

    A CSV body has nowhere to carry pagination metadata."""
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)

    response = test_client.get("/api/v1/data?format=csv&limit=1000")

    assert response.status_code == 200
    assert response.headers["x-total-count"] == "100"
    assert 'rel="next"' in response.headers["link"]
    assert "offset=10" in response.headers["link"]
    assert "format=csv" in response.headers["link"]

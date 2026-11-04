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

@pytest.mark.parametrize("limit, status", [(10, 200), (11, 422)])
def test_json_limit_is_at_most_the_page_size(monkeypatch, test_client, sql_capture, limit, status):
    """Test that a JSON limit above the page size is rejected before any SQL runs.

    JSON is paginated, so nothing becomes unreachable; CSV takes larger limits."""
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)

    response = test_client.get(f"/api/v1/data?limit={limit}")

    assert response.status_code == status, response.text
    if status == 422:
        assert [e["loc"] for e in response.json()["detail"]] == [["query", "limit"]]
        assert sql_capture == []


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


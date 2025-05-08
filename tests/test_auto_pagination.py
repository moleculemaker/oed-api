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
async def test_pagination_navigation(monkeypatch):
    """Test navigation through paginated results."""
    # Skip this test for now - we'll address it separately
    # This test requires more complex mocking of the request/response cycle
    pytest.skip("This test will be implemented in a separate PR")
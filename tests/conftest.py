import asyncio
import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import patch, AsyncMock

from asyncpg.pool import Pool
import asyncpg
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.database import Database, get_db


# Let pytest-asyncio manage the event loop
# We don't define our own event_loop fixture to avoid warnings


class MockDatabase(Database):
    """Mock database for testing that captures SQL queries."""
    
    def __init__(self, custom_fetch=None, custom_fetchval=None):
        super().__init__()
        self.executed_queries = []
        self.pool = True  # Fake pool to avoid connection attempts
        self.custom_fetch = custom_fetch
        self.custom_fetchval = custom_fetchval
    
    async def connect(self) -> None:
        """Mock connect method."""
        pass
    
    async def disconnect(self) -> None:
        """Mock disconnect method."""
        pass
    
    async def fetch(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Capture query and return a result set."""
        self.executed_queries.append({"query": query, "args": args})
        
        if self.custom_fetch:
            # If a custom function is provided, use it
            return self.custom_fetch(self, query, *args, **kwargs)
        
        return []  # Return empty list as a default response
    
    async def fetchval(self, query: str, *args, **kwargs) -> Any:
        """Capture query and return a default value."""
        self.executed_queries.append({"query": query, "args": args})
        
        if self.custom_fetchval:
            # If a custom function is provided, use it
            return self.custom_fetchval(self, query, *args, **kwargs)
        
        return 0  # Return 0 as a default value
    
    async def execute(self, query: str, *args, **kwargs) -> str:
        """Capture query and return a default result."""
        self.executed_queries.append({"query": query, "args": args})
        return ""  # Return empty string as a default result


@pytest.fixture
def mock_db(request):
    """Fixture to provide a MockDatabase instance.
    
    This fixture can be parametrized to customize the behavior of the mock database.
    Example:
    @pytest.mark.parametrize(
        "mock_db",
        [{"fetch": custom_fetch_function, "fetchval": custom_fetchval_function}],
        indirect=True
    )
    """
    if hasattr(request, "param"):
        # Handle parametrized test
        custom_fetch = request.param.get("fetch")
        custom_fetchval = request.param.get("fetchval")
        return MockDatabase(custom_fetch=custom_fetch, custom_fetchval=custom_fetchval)
    else:
        # Default case
        return MockDatabase()


@pytest.fixture
def test_client(mock_db) -> TestClient:
    """Create a FastAPI test client with overridden database dependency."""
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
def sql_capture(mock_db):
    """Fixture to provide access to captured SQL queries."""
    mock_db.executed_queries.clear()
    yield mock_db.executed_queries
import pytest

from app.core.config import settings

DATA = "/api/v1/data?ec=1.1.1.1"
TOO_BIG = 2**63  # one past Postgres bigint

# Out-of-range values used to reach the SQL: negative or oversized ones made
# Postgres fail (a 500 carrying the Postgres error), and limit=0 returned no rows.
REJECTED = [
    ("limit", -1),
    ("limit", 0),
    ("limit", TOO_BIG),
    ("offset", -5),
    ("offset", TOO_BIG),
]

ACCEPTED = [
    ("limit", 1),
    ("offset", 0),
    ("offset", TOO_BIG - 1),
]


@pytest.mark.parametrize("param, value", REJECTED)
def test_out_of_range_pagination_is_rejected(test_client, sql_capture, param, value):
    response = test_client.get(f"{DATA}&{param}={value}")

    assert response.status_code == 422, response.text
    assert [e["loc"] for e in response.json()["detail"]] == [["query", param]]
    assert sql_capture == []


@pytest.mark.parametrize("param, value", ACCEPTED)
def test_pagination_bounds_are_inclusive(test_client, sql_capture, param, value):
    response = test_client.get(f"{DATA}&{param}={value}")

    assert response.status_code == 200, response.text
    data_query = [q["query"] for q in sql_capture if "COUNT(*)" not in q["query"]][0]
    assert f"{param.upper()} {value}" in data_query


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_db",
    [{"fetchval": lambda self, query, *args: 25, "fetch": lambda self, query, *args: []}],
    indirect=True,
)
async def test_previous_past_the_end_goes_to_the_last_records(monkeypatch, test_client, mock_db):
    """Past the end, `previous` used to point at another empty page."""
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 10)

    data = test_client.get("/api/v1/data?offset=100&limit=10").json()

    assert data["data"] == []
    assert "offset=15" in data["previous"]
    assert "next" not in data

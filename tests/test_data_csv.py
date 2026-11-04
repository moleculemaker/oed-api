import csv
from io import StringIO
from unittest.mock import AsyncMock, patch

import pytest

import app.routers.data as data_router
from app.core.config import settings


@pytest.fixture
def db_calls():
    """Mock the DB query functions; iter_filtered_data yields the rows in db_calls.rows."""
    class Calls:
        rows = []
        streamed_params = []
        rows_closed = False

    async def iter_filtered_data(db, params):
        Calls.streamed_params.append(params.model_copy())
        try:
            for row in Calls.rows:
                yield row
        finally:
            Calls.rows_closed = True

    with (
        patch.object(data_router, "iter_filtered_data", iter_filtered_data),
        patch.object(data_router, "get_total_count", AsyncMock()) as count,
        patch.object(data_router, "get_filtered_data", AsyncMock()) as fetch,
    ):
        Calls.get_total_count, Calls.get_filtered_data = count, fetch
        yield Calls


def get_csv(client, query="ec=1.1.1.1"):
    return client.get(f"/api/v1/data?{query}&format=csv")


def parse(response):
    assert response.status_code == 200, response.text
    return list(csv.reader(StringIO(response.text)))


def make_row(**overrides):
    row = {"ec": "1.1.1.1", "substrate": 'ethanol, "absolute"', "organism": "Homo sapiens", "kcat_value": 7.5}
    row.update(overrides)
    return row


def test_csv_header_comes_from_the_rows(test_client, db_calls):
    db_calls.rows = [make_row()]

    assert parse(get_csv(test_client)) == [
        ["ec", "substrate", "organism", "kcat_value"],
        ["1.1.1.1", 'ethanol, "absolute"', "Homo sapiens", "7.5"],
    ]


def test_csv_header_follows_requested_columns(test_client, db_calls):
    db_calls.rows = [{"organism": "Homo sapiens", "ec": "1.1.1.1"}]

    assert parse(get_csv(test_client, "columns=ec&columns=organism")) == [
        ["ec", "organism"], ["1.1.1.1", "Homo sapiens"],
    ]


def test_csv_has_header_when_no_rows_match(test_client, db_calls):
    assert parse(get_csv(test_client, "columns=ec&columns=organism")) == [["ec", "organism"]]


def test_csv_without_limit_returns_all_rows_up_to_cap(test_client, db_calls, monkeypatch):
    monkeypatch.setattr(settings, "AUTO_PAGINATION_THRESHOLD", 2)
    monkeypatch.setattr(data_router, "MAX_DATA_LIMIT", 3)
    db_calls.rows = [make_row(ec=f"1.1.1.{i}") for i in range(3)]
    rows = parse(get_csv(test_client, "offset=7"))

    # More rows than the JSON page size, all in one file
    assert [r[0] for r in rows[1:]] == ["1.1.1.0", "1.1.1.1", "1.1.1.2"]
    # One row past the cap is requested, so an oversized result can be detected
    assert db_calls.streamed_params[0].limit == 4
    assert db_calls.streamed_params[0].offset == 7
    db_calls.get_total_count.assert_not_awaited()
    db_calls.get_filtered_data.assert_not_awaited()


def test_csv_without_limit_rejects_more_rows_than_cap(test_client, db_calls, monkeypatch):
    monkeypatch.setattr(data_router, "MAX_DATA_LIMIT", 3)
    db_calls.rows = [make_row() for _ in range(4)]
    response = get_csv(test_client)

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Query matches more than 3 records")
    # The row iterator, and so the DB cursor, is closed as soon as the cap is passed
    assert db_calls.rows_closed


def test_csv_with_limit_is_not_capped(test_client, db_calls, monkeypatch):
    monkeypatch.setattr(data_router, "MAX_DATA_LIMIT", 3)
    db_calls.rows = [make_row() for _ in range(4)]
    rows = parse(get_csv(test_client, "limit=50&offset=100"))

    assert len(rows) == 5
    assert db_calls.streamed_params[0].limit == 50
    assert db_calls.streamed_params[0].offset == 100


def test_csv_accepts_limits_above_json_cap(test_client, db_calls):
    for limit in (settings.AUTO_PAGINATION_THRESHOLD + 1, data_router.MAX_DATA_LIMIT):
        parse(get_csv(test_client, f"limit={limit}"))

    assert [p.limit for p in db_calls.streamed_params] == [
        settings.AUTO_PAGINATION_THRESHOLD + 1, data_router.MAX_DATA_LIMIT,
    ]


def test_csv_rejects_limit_above_cap(test_client, db_calls):
    response = get_csv(test_client, f"limit={data_router.MAX_DATA_LIMIT + 1}")

    assert response.status_code == 422
    assert [e["loc"] for e in response.json()["detail"]] == [["query", "limit"]]
    assert db_calls.streamed_params == []


def test_csv_db_error_mid_result_returns_500(test_client):
    async def failing_rows(db, params):
        yield make_row()
        raise RuntimeError("connection lost")

    with patch.object(data_router, "iter_filtered_data", failing_rows):
        response = get_csv(test_client)

    assert response.status_code == 500
    assert "connection lost" in response.json()["detail"]


def test_csv_spills_large_output_to_disk(test_client, db_calls):
    db_calls.rows = [make_row(substrate="C" * 100_000) for _ in range(100)]
    rows = parse(get_csv(test_client))

    assert len(rows) == 101
    assert all(len(r[1]) == 100_000 for r in rows[1:])


async def test_closing_iter_filtered_data_closes_the_cursor():
    from contextlib import aclosing

    from app.db.database import Database
    from app.db.queries import iter_filtered_data
    from app.models.query_params import OEDDataQueryParams

    closed = []

    async def iterate(query, *args):
        try:
            yield make_row()
            yield make_row()
        finally:
            closed.append(True)

    db = Database()
    db.iterate = iterate
    async with aclosing(iter_filtered_data(db, OEDDataQueryParams(limit=2))) as rows:
        await anext(rows)

    assert closed == [True]


async def test_write_csv_closes_rows_when_over_cap():
    from fastapi import HTTPException

    closed = []

    async def rows():
        try:
            for _ in range(5):
                yield make_row()
        finally:
            closed.append(True)

    # Holding a reference means only an explicit close, not garbage collection, can close it
    generator = rows()
    with pytest.raises(HTTPException) as error:
        await data_router.write_csv(generator, fieldnames=None, max_rows=3)

    assert error.value.status_code == 400
    assert closed == [True]

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from Challenge.mainapi import app

client = TestClient(app)


@pytest.fixture
def valid_update_request():
    return {
        "table": "sales_summary_by_product_family",
        "column": "quantity",
        "value": "14",
        "condition": "supplier = 'Smith Ltd' AND family = 'impact'",
        "level": 1,
    }


@pytest.fixture
def redis_mock():
    with patch("Challenge.mainapi.redis_client", new_callable=AsyncMock) as mock_redis:
        mock_redis.ping.return_value = True
        mock_redis.xadd.return_value = "stream_id"
        mock_redis.xrange.return_value = [{"key": "value"}]
        yield mock_redis


@pytest.fixture
def duckdb_mock():
    with patch("Challenge.mainapi.DuckDBManager", autospec=True) as mock_duckdb:
        instance = mock_duckdb.return_value
        instance.execute_query_async = AsyncMock(return_value=None)
        yield instance


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Liquid Duck API!"}

@pytest.mark.asyncio
async def test_update_cell_success(valid_update_request, redis_mock, duckdb_mock):
    """
    Test the update_cell endpoint with generalized query validation.
    """
    with patch("Challenge.mainapi.redis_client", redis_mock), patch(
        "Challenge.mainapi.db_manager", duckdb_mock
    ):
        response = client.post("/update_cell", json=valid_update_request)

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        assert duckdb_mock.execute_query_async.call_count == 2

        calls = [call.args[0] for call in duckdb_mock.execute_query_async.call_args_list]
        assert any("SELECT 1;" in query for query in calls), "Connection check query missing."
        assert any(
            f"UPDATE {valid_update_request['table']}" in query and
            f"SET {valid_update_request['column']} = '{valid_update_request['value']}'" in query and
            f"WHERE {valid_update_request['condition']}" in query
            for query in calls
        ), f"Update query missing or malformed. Actual calls: {calls}"
        redis_mock.xadd.assert_called_once()


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        ({"table": "", "column": "quantity", "value": "14", "condition": "x = 1", "level": 1}, 400),
        ({"table": "non_existing_table", "column": "quantity", "value": "14", "condition": "x = 1", "level": 1}, 500),
    ],
)
def test_update_cell_invalid_cases(payload, expected_status, redis_mock, duckdb_mock):
    response = client.post("/update_cell", json=payload)
    assert response.status_code == expected_status


def test_get_updates(redis_mock):
    response = client.get("/get_updates")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    redis_mock.xrange.assert_called_once()

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_redis_client():
    with patch("aioredis.from_url") as mock_redis:
        redis_mock = AsyncMock()
        mock_redis.return_value = redis_mock
        yield redis_mock


@pytest.mark.asyncio
async def test_redis_stream(mock_redis_client):
    redis_client = mock_redis_client

    await redis_client.xadd("request_duck", {"data": '{"key": "value"}'})
    redis_client.xread.return_value = [
        ("request_duck", [(0, {"data": '{"key": "value"}'})])
    ]

    messages = await redis_client.xread({"request_duck": "0"}, count=1)
    assert len(messages) > 0
    assert messages[0][1][0][1]["data"] == '{"key": "value"}'

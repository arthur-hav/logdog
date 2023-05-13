from api.repository.repository import PostgresRepository
import pytest


@pytest.mark.asyncio
async def test_flatten():
    repo = PostgresRepository(123)

    iter_dct = [v async for v in repo.flatten_dict("test", {"test": {"a": "1", "b": ["c", "d"]}})]

    assert iter_dct == [("test.a", "1"), ("test.b.0", "c"), ("test.b.1", "d")]

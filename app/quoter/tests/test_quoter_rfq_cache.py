"""Tests for health checker."""

import json
from pathlib import Path
from typing import Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from hexbytes import HexBytes

from app.evm.helpers import uuid_to_topic
from app.protocols.liquorice.schemas import RFQMessage

EXAMPLE_RFQ_MESSAGE_DICT = json.loads(
    (
        Path(__file__).parent.parent.parent
        / "protocols/liquorice/tests/data"
        / "liquorice_rfq.json"
    ).read_text()
)["message"]


@pytest.fixture
def generate_rfq():
    """Fixture to generate RFQ messages."""

    def _generate_rfq() -> Tuple[HexBytes, RFQMessage]:
        """Generate a sample RFQMessage with a random UUID."""
        rfq_data = EXAMPLE_RFQ_MESSAGE_DICT.copy()
        rfq_data["rfqId"] = str(uuid4())
        rfq: RFQMessage = RFQMessage.model_validate(rfq_data)
        cache_key: HexBytes = uuid_to_topic(rfq.rfqId)
        return cache_key, rfq

    return _generate_rfq


@pytest.fixture
def rfq_cache_with_time_mock():
    """Fixture to mock time.monotonic for TTL cache testing."""
    # TTLCache uses time.monotonic by default, so we need to patch that specifically
    with patch("time.monotonic") as monotonic_mock:
        start_time = 1754000000.0

        # Create a controllable time source
        mock_controller = MagicMock()
        mock_controller.current_time = start_time

        def get_monotonic_time():
            return mock_controller.current_time

        # Apply mock to monotonic time
        monotonic_mock.side_effect = get_monotonic_time

        # Import RFQCache here instead of global to have it use the mocked time
        from app.quoter.cache import RFQCache

        rfq_cache = RFQCache()
        yield mock_controller, rfq_cache


@pytest.mark.asyncio
async def test_cache_lifecycle(rfq_cache_with_time_mock, generate_rfq):
    """Test the lifecycle of RFQ cache with TTL."""
    # constants imported here to avoid premature loading before applying time patch
    from app.quoter.cache import CACHE_MAXSIZE, CACHE_TTL

    mock_time, rfq_cache = rfq_cache_with_time_mock
    start_time = 1754000000.0
    mock_time.current_time = start_time
    # Check initial state
    assert rfq_cache._cache.maxsize == CACHE_MAXSIZE
    assert rfq_cache._cache.ttl == CACHE_TTL
    assert len(rfq_cache._cache) == 0

    # Add first RFQ to cache
    first_key, first_rfq = generate_rfq()
    await rfq_cache.add_rfq(first_rfq)
    assert len(rfq_cache._cache) == 1
    assert await rfq_cache.get_rfq_by_topic(first_key) == first_rfq

    # just before first-rfq TTL expired
    mock_time.current_time = start_time + CACHE_TTL - 1
    assert await rfq_cache.get_rfq_by_topic(first_key) == first_rfq
    assert len(rfq_cache._cache) == 1
    assert rfq_cache._cache.expire() == []
    assert len(rfq_cache._cache) == 1

    # Add second RFQ to cache
    second_key, second_rfq = generate_rfq()
    await rfq_cache.add_rfq(second_rfq)
    assert len(rfq_cache._cache) == 2
    assert await rfq_cache.get_rfq_by_topic(first_key) == first_rfq
    assert await rfq_cache.get_rfq_by_topic(second_key) == second_rfq
    assert rfq_cache._cache.expire() == []

    # One second later, first rfq should expire
    mock_time.current_time = start_time + CACHE_TTL
    assert len(rfq_cache._cache) == 1
    assert rfq_cache._cache.expire() == []  # expired on len() call so has no effect here
    assert await rfq_cache.get_rfq_by_topic(first_key) is None  # expired
    assert await rfq_cache.get_rfq_by_topic(second_key) == second_rfq

    # one second before 2nd rfq expires
    mock_time.current_time = start_time + CACHE_TTL * 2 - 2
    assert rfq_cache._cache.expire() == []
    assert await rfq_cache.get_rfq_by_topic(second_key) == second_rfq

    # One second later, second rfq should expire as well
    mock_time.current_time = start_time + CACHE_TTL * 2 - 1
    expired_items = rfq_cache._cache.expire()
    assert len(expired_items) == 1
    assert expired_items[0][0] == second_key
    assert expired_items[0][1] == second_rfq
    assert await rfq_cache.get_rfq_by_topic(second_key) is None
    assert len(rfq_cache._cache) == 0

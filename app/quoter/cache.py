import asyncio
from typing import Optional

from cachetools import TTLCache
from hexbytes import HexBytes

from app.evm.helpers import uuid_to_topic
from app.protocols.liquorice.schemas import RFQMessage

CACHE_MAXSIZE = 10000
CACHE_TTL = 60 * 5  # 5 minutes


class RFQCache:
    """Thread-safe expireable caching singleton for rfq data data."""

    _cache: TTLCache[HexBytes, RFQMessage]
    _lock: asyncio.Lock

    def __init__(self) -> None:
        self._cache: TTLCache[HexBytes, RFQMessage] = TTLCache(
            maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL
        )
        self._lock = asyncio.Lock()

    async def add_rfq(self, rfq: RFQMessage):
        """Add RFQ to the cache."""
        async with self._lock:
            self._cache[uuid_to_topic(rfq.rfqId)] = rfq

    async def get_rfq_by_topic(self, topic: HexBytes) -> Optional[RFQMessage]:
        """Get RFQ by topic from the cache."""
        async with self._lock:
            return self._cache.get(topic)

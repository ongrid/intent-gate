"""A service to handle RFQs and send quotes"""

import asyncio
from contextlib import suppress
from logging import getLogger
from typing import AsyncIterator

from app.markets.markets import MarketState
from app.protocols.liquorice.schemas import RFQMessage, RFQQuoteMessage

log = getLogger(__name__)


class LiquoriceQuoter:
    """Responder service singleton that reads RFQs from a queue
    and sends quotes back (if quoting conditions satisfy)"""

    in_rfqs: asyncio.Queue[RFQMessage]
    out_quotes: asyncio.Queue[RFQQuoteMessage]
    markets: MarketState

    def __init__(
        self,
        in_rfqs: asyncio.Queue[RFQMessage],
        out_quotes: asyncio.Queue[RFQQuoteMessage],
        markets: MarketState,
    ) -> None:
        self.in_rfqs = in_rfqs
        self.out_quotes = out_quotes
        self.markets = markets

    async def rfq_stream(self) -> AsyncIterator[RFQMessage]:
        """Stream RFQs from the input queue."""
        while True:
            rfq = await self.in_rfqs.get()
            try:
                yield rfq
            finally:
                self.in_rfqs.task_done()

    async def run(self) -> None:
        """Process RFQs from queue until cancelled."""
        with suppress(asyncio.CancelledError):
            async for rfq in self.rfq_stream():
                try:
                    log.debug("Processing RFQ: %s", rfq)
                    # Process RFQ here
                except Exception as e:  # pylint: disable=broad-exception-caught
                    log.error("Failed to process RFQ: %s", e)

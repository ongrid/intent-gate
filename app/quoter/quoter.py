"""A service to handle RFQs and send quotes"""

import asyncio
from contextlib import suppress
from decimal import Decimal
from logging import getLogger
from typing import AsyncIterator

from hexbytes import HexBytes
from web3.main import to_checksum_address

from app.evm.const import ERC20_ZERO_ADDRESS as ZERO_ADDRESS
from app.markets.markets import MarketState
from app.metrics.metrics import metrics
from app.protocols.liquorice.schemas import QuoteLevelLite, RFQMessage, RFQQuoteMessage
from app.protocols.liquorice.signer import Web3Signer

log = getLogger(__name__)


class LiquoriceQuoter:
    """Responder service singleton that reads RFQs from a queue
    and sends quotes back (if quoting conditions satisfy)"""

    in_rfqs: asyncio.Queue[RFQMessage]
    out_quotes: asyncio.Queue[RFQQuoteMessage]
    markets: MarketState
    signer: Web3Signer

    def __init__(
        self,
        in_rfqs: asyncio.Queue[RFQMessage],
        out_quotes: asyncio.Queue[RFQQuoteMessage],
        markets: MarketState,
        signer: Web3Signer,
    ) -> None:
        self.in_rfqs = in_rfqs
        self.out_quotes = out_quotes
        self.markets = markets
        self.signer = signer

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
                    metrics_labels = {
                        "chain_id": rfq.chainId,
                        "solver": rfq.solver,
                        "base_token": rfq.baseToken,
                        "quote_token": rfq.quoteToken,
                    }
                    base_token = self.markets.get_token(rfq.baseToken, rfq.chainId)
                    if not base_token:
                        log.info(
                            "BaseToken %s unsupported. Ignoring RFQ: %s", rfq.baseToken, rfq.rfqId
                        )
                        metrics.rfqs_total.labels(**metrics_labels, status="UNSUPPORTED_BT").inc()
                        continue
                    quote_token = self.markets.get_token(rfq.quoteToken, rfq.chainId)
                    if not quote_token:
                        log.info(
                            "QuoteToken %s unsupported. Ignoring RFQ: %s",
                            rfq.quoteToken,
                            rfq.rfqId,
                        )
                        metrics.rfqs_total.labels(**metrics_labels, status="UNSUPPORTED_QT").inc()
                        continue
                    path = self.markets.shortest_path(base_token, quote_token)
                    assert path, "No path found for RFQ"
                    assert isinstance(rfq.baseTokenAmount, int)
                    assert rfq.baseTokenAmount > 0
                    receive_base_token_amount = base_token.raw_to_decimal(rfq.baseTokenAmount)
                    send_quote_token_amount = min(
                        receive_base_token_amount * Decimal("1.05"), quote_token.balance
                    )
                    send_quote_token_raw_amount = quote_token.decimal_to_raw(
                        send_quote_token_amount
                    )
                    if send_quote_token_amount == 0:
                        log.info(
                            "No quote tokens available for RFQ %s: %s",
                            rfq.rfqId,
                            rfq.quoteToken,
                        )
                        metrics.rfqs_total.labels(**metrics_labels, status="LOW_QT_BALANCE").inc()
                        continue
                    quote_lvl = QuoteLevelLite(
                        baseToken=base_token.address,
                        quoteToken=quote_token.address,
                        baseTokenAmount=int(rfq.baseTokenAmount),
                        quoteTokenAmount=send_quote_token_raw_amount,
                        expiry=rfq.expiry + 30,
                        settlementContract=to_checksum_address(ZERO_ADDRESS),
                        minQuoteTokenAmount=1,
                        signer=to_checksum_address(
                            ZERO_ADDRESS
                        ),  # Placeholder, will be set later by Web3 Signer
                        recipient=to_checksum_address(ZERO_ADDRESS),  # Placeholder
                        signature=HexBytes("00" * 65),  # Placeholder
                    )
                    non_signed_quote = RFQQuoteMessage(rfqId=rfq.rfqId, levels=[quote_lvl])
                    signed_quote = self.signer.sign_quote_levels(rfq, non_signed_quote)
                    if not signed_quote:
                        log.error("Failed to sign quote for RFQ: %s", rfq.rfqId)
                        continue
                    log.info("Sending quote for RFQ %s: %s", rfq.rfqId, signed_quote)
                    await self.out_quotes.put(signed_quote)
                    metrics.rfqs_total.labels(**metrics_labels, status="QUOTE_SENT").inc()

                except Exception as e:  # pylint: disable=broad-exception-caught
                    log.error("Failed to process RFQ: %s", e)
                    metrics.rfqs_total.labels(
                        **metrics_labels, status="QUOTER_UNHANDLED_EXC"
                    ).inc()

import asyncio
from logging import getLogger

import websockets
from pydantic import ValidationError
from websockets.asyncio.client import ClientConnection

from app.config.maker import MakerConfig

from .schemas import LiquoriceEnvelope, MessageType, RFQMessage, RFQQuoteMessage

LIQUORICE_WS_URL = "wss://api.liquorice.tech/v1/maker/ws"
LIQUORICE_WS_RETRY_DELAY = 5  # seconds

log = getLogger(__name__)


class LiquoriceClient:
    """Client for connecting to the Liquorice WebSocket API.
    Relays RFQs and quotes between the queues and the WebSocket."""

    out_rfqs: asyncio.Queue[RFQMessage]
    in_quotes: asyncio.Queue[RFQQuoteMessage]
    _stop_event: asyncio.Event

    def __init__(self, cfg_maker: MakerConfig) -> None:
        self.out_rfqs = asyncio.Queue()
        self.in_quotes = asyncio.Queue()
        self.uri = LIQUORICE_WS_URL
        self.headers = {
            "maker": cfg_maker.maker,
            "authorization": cfg_maker.authorization,
        }
        self.out_rfqs: asyncio.Queue[RFQMessage] = asyncio.Queue()  # Queue for outgoing RFQs
        self.in_quotes: asyncio.Queue[RFQQuoteMessage] = (
            asyncio.Queue()
        )  # Queue for incoming quotes
        self._stop_event = asyncio.Event()

    async def _reader(self, ws: ClientConnection) -> None:
        """Reads messages from the WebSocket and puts them into the rfqs queue."""
        try:
            async for message in ws:
                if self._stop_event.is_set():
                    log.debug("Reader task stopped due to stop event")
                    return
                log.debug("Rcvd: %s", message)
                try:
                    rfq = LiquoriceEnvelope.model_validate_json(message)
                    if rfq.messageType == MessageType.CONNECTED:
                        log.debug("Message type CONNECTED received, ignoring")
                        continue
                    elif rfq.messageType == MessageType.RFQ:
                        log.debug("Message type RFQ received, processing")
                        await self.out_rfqs.put(rfq.message)
                    else:
                        log.warning("Unexpected message type Rcvd: %s", rfq.messageType)
                except ValidationError as e:
                    log.error("Validation error: %s", e)
                    continue
        except asyncio.CancelledError:
            log.debug("Reader task cancelled")
            raise
        except Exception as e:
            log.exception("Exception while reading from WS: %s", e)
            raise

    async def _writer(self, ws: ClientConnection) -> None:
        """Reads quote from the quotes queue and sends them over the WebSocket."""
        try:
            while not self._stop_event.is_set():
                quote_msg = await self.in_quotes.get()
                assert isinstance(quote_msg, RFQQuoteMessage), "Expected RFQQuoteMessage"
                raw_msg = LiquoriceEnvelope(
                    message=quote_msg, messageType=MessageType.RFQ_QUOTE
                ).model_dump_json(exclude_none=True)
                await ws.send(raw_msg)
                log.debug("Sent: %s", raw_msg)
        except asyncio.CancelledError:
            log.debug("Writer task cancelled")
            raise
        except Exception as e:
            log.exception("Writer task exception: %s", e)
            raise

    async def run(self) -> None:
        """Connects to the Liquorice WebSocket and starts reading and writing messages."""
        attempt = 0
        while not self._stop_event.is_set():
            attempt += 1
            log.info("Connecting to Liquorice WS, attempt: %s, url: %s", attempt, self.uri)
            try:
                async with websockets.connect(self.uri, additional_headers=self.headers) as ws:
                    log.info("Connected to Liquorice WebSocket at %s", self.uri)
                    # Start the reader and writer tasks
                    reader_task = asyncio.create_task(self._reader(ws))
                    writer_task = asyncio.create_task(self._writer(ws))
                    done, pending = await asyncio.wait(
                        {reader_task, writer_task}, 
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancel remaining tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            # Ignore since we are cancelling
                            pass
                    
                    # Handle the completed task
                    for task in done:
                        try:
                            await task
                        except Exception as e:
                            log.exception("Task failed: %s", e)
                            # Propagate the root reason of failure
                            raise

            except asyncio.CancelledError:
                log.info("LiquoriceClient cancelled, stopping...")
                self._stop_event.set()
                raise
            except Exception as e:
                log.exception(
                    "Unexpected error in LiquoriceClient: %s. Retrying after %s s",
                    e,
                    LIQUORICE_WS_RETRY_DELAY,
                )
                await asyncio.sleep(LIQUORICE_WS_RETRY_DELAY)

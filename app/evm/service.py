"""ChainService module for managing cuncurrent web3 event listeners and processing."""

import asyncio
from logging import getLogger
from typing import List, Optional

from web3 import AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.persistent import WebSocketProvider
from web3.utils.subscriptions import (
    LogsSubscription,
    LogsSubscriptionContext,
)

from app.evm.const import ERC20_TRANSFER_TOPIC, ERC20_ZERO_ADDRESS
from app.evm.helpers import encode_address
from app.evm.registry import ChainRegistry

from ..schemas.chain import Chain

log = getLogger(__name__)


class ChainServiceMgr:  # pylint: disable=too-few-public-methods
    """Singleton manager for ChainServices."""

    services: List["ChainService"] = []

    def __init__(self, chain_registry: ChainRegistry):
        self.chain_registry = chain_registry
        self.services: List["ChainService"] = []
        for chain in self.chain_registry.chains:
            self.services.append(ChainService(self, chain))

    async def run(self) -> None:
        """Run all chain services."""
        log.info("Starting ChainServiceManager with %d services", len(self.services))
        for service in self.services:
            if not service.is_running:
                log.info("Starting ChainService for %s Chain", service.chain.short_names[0])
                await service.start()

    async def shutdown(self) -> None:
        """Shutdown all chain services."""
        log.info("Shutting down ChainServiceManager with %d services", len(self.services))
        for service in self.services:
            if service.is_running:
                log.info("Stopping ChainService for %s", service.chain.name)
                await service.stop()
            else:
                log.warning("ChainService for %s is already stopped", service.chain.name)
            service.is_running = False
        log.info("All ChainServices have been stopped.")


class ChainService:
    """Service for managing blockchain event listeners and processing."""

    chain: Chain
    is_running: bool = False
    mgr: ChainServiceMgr
    task: Optional[asyncio.Task] = None
    conn_closed = asyncio.Event
    watchdog_task = Optional[asyncio.Task]

    def __init__(self, mgr: ChainServiceMgr, chain: Chain):
        self.mgr = mgr
        self.chain = chain
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.subscription_handler_task: Optional[asyncio.Task] = None

    async def log_handler(
        self,
        handler_context: LogsSubscriptionContext,
    ) -> None:
        """Handle logs from the subscription manager to catch potential balance changes."""
        assert self.chain is not None, "Chain must be set before handling logs"
        log_receipt = handler_context.result
        log.debug("Log receipt: %s chain: %s", log_receipt, self.chain.name)

    def build_tokens_subscription_filter_with_handlers(self, chain) -> List[LogsSubscription]:
        """Build a filter for ERC20 token transfers."""
        result = []
        for token in chain.tokens:
            for address_to_monitor in ERC20_ZERO_ADDRESS, chain.liquorice_settlement_address:
                # monitor transfers TO the address of interest
                result.append(
                    LogsSubscription(
                        address=token.address,
                        topics=[
                            ERC20_TRANSFER_TOPIC,
                            None,  # type: ignore[list-item] # Match any from address
                            encode_address(address_to_monitor),
                        ],
                        handler=self.log_handler,
                    )
                )
                # monitor transfers FROM the address of interest
                result.append(
                    LogsSubscription(
                        address=token.address,
                        topics=[
                            ERC20_TRANSFER_TOPIC,
                            encode_address(address_to_monitor),
                            None,  # type: ignore[list-item] # Match any to address
                        ],
                        handler=self.log_handler,
                    )
                )
        return result

    async def connect_web3_subscribe_and_process(self) -> None:
        """Example of using a context manager for subscription."""
        async with AsyncWeb3(WebSocketProvider(self.chain.ws_rpc_url)) as w3:
            chain_id = await w3.eth.chain_id
            assert self.chain == self.mgr.chain_registry.get_chain_by_id(chain_id)
            log.info("Connected to chain ID: %s %s", chain_id, self.chain.name)
            if self.chain.poa:
                log.info("Using POA middleware for chain %s", self.chain.name)
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            await w3.subscription_manager.subscribe(
                self.build_tokens_subscription_filter_with_handlers(self.chain)
            )
            self.subscription_handler_task = asyncio.create_task(
                w3.subscription_manager.handle_subscriptions()
            )
            log.info("Web3 subscription manager started for %s", self.chain.name)
            await self.subscription_handler_task
            log.info("Subscription ended, closing connection.")

    async def start(self) -> None:
        """Start all chain service workers."""
        if self.is_running:
            log.warning("ChainService for %s is already running", self.chain.name)
            return
        log.info("Starting Chain Service for %s", self.chain.short_names[0])
        self.task = asyncio.create_task(self.connect_web3_subscribe_and_process())
        self.is_running = True

    async def stop(self) -> None:
        """Stop all chain service workers."""
        self.is_running = False
        assert self.task is not None, "Task must be set before stopping"
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        self.task = None

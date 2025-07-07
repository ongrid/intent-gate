import asyncio
from logging import getLogger
from typing import Optional

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.contract import AsyncContract

from app.markets.markets import MarketState
from app.schemas.chain import Chain

log = getLogger(__name__)

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]
ERC20_UPDATE_INTERVAL = 10  # seconds, how often to update balances
ERC20_MIN_UPDATE_DELAY = 0.1  # seconds, minimum delay between updates


class ERC20Service:
    """Service for reading and updating ERC-20 token balances"""

    chain: Chain
    w3: AsyncWeb3
    task: Optional[asyncio.Task]
    is_running: bool
    markets: MarketState
    _immediate_read_requested: asyncio.Event

    def __init__(self, chain: Chain, w3: AsyncWeb3, markets: MarketState) -> None:
        assert isinstance(chain, Chain), "Chain must be an instance of Chain"
        assert isinstance(markets, MarketState), "Markets must be an instance of MarketState"
        log.debug("Initializing ERC20Service for %s", chain.name)
        assert chain.active, "Chain must be active to create ERC20Service"
        self.chain = chain
        self.w3 = w3
        self.markets = markets
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self._immediate_read_requested = asyncio.Event()

    def request_immediate_read(self) -> None:
        """Called by ChainService when a token transfer event is received.

        Call signals that the ERC-20 service should immediately rescan
        token balances rather than waiting for the next periodic update cycle."""
        log.info("Immediate token balances update requested for %s", self.chain.name)
        self._immediate_read_requested.set()

    async def get_token_raw_balance(
        self, token_address: ChecksumAddress, account_address: ChecksumAddress
    ) -> int:
        """Get token balance for a specific account."""
        try:
            contract: AsyncContract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            raw_balance = await contract.functions.balanceOf(account_address).call()
            return int(raw_balance)
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(
                "Error getting balance for token %s, account %s: %s",
                token_address,
                account_address,
                e,
            )
            return 0

    async def run_loop(self) -> None:
        """Main loop to periodically read ERC-20 token balances and update market graph."""
        log.info("Starting ERC-20 balance update loop for %s", self.chain.name)
        self.is_running = True
        while self.is_running:
            try:
                start_time = asyncio.get_event_loop().time()
                block_number = await self.w3.eth.block_number
                for token in self.markets.get_tokens_by_chain_id(self.chain.id):
                    assert self.chain.skeeper_address
                    raw_balance: int = await self.get_token_raw_balance(
                        token.address, self.chain.skeeper_address
                    )
                    log.info(
                        "Token %s balance for %s: %d",
                        token.symbol,
                        self.chain.skeeper_address,
                        raw_balance,
                    )
                    # Update the market state with the new balance
                    token.raw_balance = raw_balance
                    token.last_updated_block = block_number
                update_duration = asyncio.get_event_loop().time() - start_time
                log.debug("Balance update completed in %.2f seconds", update_duration)
                sleep_time = max(ERC20_MIN_UPDATE_DELAY, ERC20_UPDATE_INTERVAL - update_duration)

                # Wait for immediate update event or timeout for next periodic update
                try:
                    await asyncio.wait_for(
                        self._immediate_read_requested.wait(), timeout=sleep_time
                    )
                    self._immediate_read_requested.clear()
                    log.debug("Immediate update triggered for %s", self.chain.name)
                except asyncio.TimeoutError:
                    # Normal timeout, continue with periodic update
                    pass
            except asyncio.CancelledError:
                log.info("Balance update loop cancelled for %s", self.chain.name)
                self.is_running = False
                break
            except Exception as e:  # pylint: disable=broad-exception-caught
                log.error("Error in balance update loop for %s: %s", self.chain.name, e)
                # Wait before retrying
                await asyncio.sleep(ERC20_UPDATE_INTERVAL)

    async def start(self) -> None:
        """Start the ERC-20 balance update service."""
        if self.is_running:
            log.warning("ERC20Service for %s is already running", self.chain.name)
            return
        log.info("Starting ERC20Service for %s", self.chain.name)
        self.task = asyncio.create_task(self.run_loop())

    async def stop(self) -> None:
        """Stop the balance monitoring service."""
        if not self.is_running:
            return

        self.is_running = False

        # pylint: disable=duplicate-code
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        log.info("ERC20Service stopped for %s", self.chain.name)

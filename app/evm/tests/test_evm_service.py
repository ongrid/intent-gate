"""Tests for ChainService class."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from web3.utils.subscriptions import LogsSubscription

from app.evm.registry import ChainRegistry
from app.evm.service import ChainService, ChainServiceMgr
from app.schemas.chain import Chain
from app.schemas.token import ERC20Token


@pytest.fixture
def mock_chain() -> Chain:
    """Create a test chain."""
    chain = Chain(
        id=123,
        name="Chain 123",
        short_names=["chain_123"],
        gas_token="GAS123",
        ws_rpc_url="wss://test.chain123.com",
        liquorice_settlement_address="0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167",
        tokens=[],
    )
    chain.tokens.append(
        ERC20Token(
            name="Token 1",
            symbol="TKN1",
            chain=chain,
            address="0xe688b84b23f322a994A53dbF8E15FA82CDB71127",
            decimals=18,
        )
    )
    chain.tokens.append(
        ERC20Token(
            name="Token 2",
            symbol="TKN2",
            chain=chain,
            address="0x9b271990873D677c93B3668f813C13770878B421",
            decimals=18,
        )
    )
    chain.tokens.append(
        ERC20Token(
            name="Token 3",
            symbol="TKN3",
            chain=chain,
            address="0x06D3b2CDC00503133090fc5ccCB027C0a636a543",
            decimals=8,
        )
    )
    return chain


@pytest.fixture
def mock_async_web3_cls(mock_chain: Chain):

    class MockSubscriptionManager:
        _max_events = 10
        _event_count = 0

        def __init__(self, *args, **kwargs) -> None:
            pass

        async def subscribe(self, *args, **kwargs) -> None:
            pass

        async def handle_subscriptions(self) -> None:
            for i in range(self._max_events):
                await asyncio.sleep(0.1)
                self._event_count += 1
                if self._event_count >= self._max_events:
                    return

    class MockAsyncWeb3:
        """Mock implementation of AsyncWeb3 for testing."""

        def __init__(self, *args, **kwargs):
            """Initialize with mocked components."""
            self._is_connected = True
            self._event_count = 0
            self._max_events = 10
            self.eth = AsyncMock()

            async def get_chain_id() -> int:
                return mock_chain.id

            self.eth.chain_id = get_chain_id()
            self.subscription_manager = MockSubscriptionManager()
            self.middleware_onion = AsyncMock()
            self.middleware_onion.inject = AsyncMock()

        async def __aenter__(self):
            """Async context manager entry."""
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """Async context manager exit."""
            return None

    return MockAsyncWeb3


@pytest.fixture
def mock_chain_service(mock_chain: Chain) -> ChainService:
    """Create a ChainService instance with mocked dependencies."""
    registry = ChainRegistry()
    registry.chains.append(mock_chain)
    registry.chain_by_id[mock_chain.id] = mock_chain

    manager = ChainServiceMgr(registry)
    return ChainService(manager, mock_chain)


@pytest.mark.asyncio
async def test_chain_service_init(mock_chain_service: ChainService):
    """Test ChainService initialization."""
    assert not mock_chain_service.is_running
    assert mock_chain_service.task is None
    assert mock_chain_service.subscription_handler_task is None
    assert mock_chain_service.chain is not None


@pytest.mark.asyncio
async def test_build_subscription_filters(mock_chain_service: ChainService):
    """Test building subscription filters."""
    filters = mock_chain_service.build_tokens_subscription_filter_with_handlers(
        mock_chain_service.chain
    )

    assert len(filters) == 12  # Two filters per token (to/from) signer and settlement address
    assert all(isinstance(f, LogsSubscription) for f in filters)


@pytest.mark.asyncio
async def test_chain_service_start_stop(mock_chain_service: ChainService):
    """Test starting and stopping chain service."""
    connect_web3_subscribe_and_process_mock = AsyncMock()
    with patch(
        "app.evm.service.ChainService.connect_web3_subscribe_and_process",
        connect_web3_subscribe_and_process_mock,
    ):
        # Test start
        await mock_chain_service.start()
        assert mock_chain_service.is_running
        assert mock_chain_service.task is not None
        assert connect_web3_subscribe_and_process_mock.called

        # Test stop
        await mock_chain_service.stop()
        assert not mock_chain_service.is_running
        assert mock_chain_service.task is None


@pytest.mark.asyncio
async def test_chain_service_start_already_running(mock_chain_service: ChainService):
    """Test starting an already running service."""
    connect_web3_subscribe_and_process_mock = AsyncMock()
    with patch(
        "app.evm.service.ChainService.connect_web3_subscribe_and_process",
        connect_web3_subscribe_and_process_mock,
    ):
        mock_chain_service.is_running = True
        await mock_chain_service.start()
        assert not connect_web3_subscribe_and_process_mock.called


@pytest.mark.asyncio
async def test_log_handler(mock_chain_service: ChainService):
    """Test log handler processing."""
    context = Mock()
    context.result = {
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "topics": ["topic1", "topic2"],
        "data": "0x",
    }

    await mock_chain_service.log_handler(context)
    # No assertion needed as we're just testing it doesn't raise


@pytest.mark.asyncio
async def test_chain_service_connect_web3_subscribe_and_process(
    mock_chain: Chain, mock_async_web3_cls
):
    """Test chain service using eth-tester provider without modifying ChainService."""
    with patch("app.evm.service.AsyncWeb3", mock_async_web3_cls):
        registry = ChainRegistry()
        registry.chains.append(mock_chain)
        registry.chain_by_id[mock_chain.id] = mock_chain
        manager = ChainServiceMgr(registry)
        chain_service = ChainService(manager, mock_chain)
        await chain_service.connect_web3_subscribe_and_process()

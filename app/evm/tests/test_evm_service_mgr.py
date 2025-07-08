"""Tests for ChainServiceMgr class."""

from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from app.evm.registry import ChainRegistry
from app.evm.service import ChainServiceMgr
from app.markets.markets import MarketState
from app.protocols.liquorice.const import LIQUORICE_SETTLEMENT_ADDRESS
from app.schemas.chain import Chain


@pytest.fixture
def mock_chains() -> List[Chain]:
    """Create a mock chain for testing."""
    return [
        Chain(
            id=123,
            name="Chain 123",
            short_names=["chain_123"],
            gas_token="GAS123",
            ws_rpc_url="wss://test.chain123.com",
            liquorice_settlement_address=LIQUORICE_SETTLEMENT_ADDRESS,
            active=True,
        ),
        Chain(
            id=124,
            name="Chain 124",
            short_names=["chain_124"],
            gas_token="GAS124",
            ws_rpc_url="wss://test.chain124.com",
            liquorice_settlement_address=LIQUORICE_SETTLEMENT_ADDRESS,
            active=True,
        ),
        Chain(
            id=125,
            name="Chain 125",
            short_names=["chain_125"],
            gas_token="GAS125",
            ws_rpc_url="wss://test.chain125.com",
            liquorice_settlement_address=LIQUORICE_SETTLEMENT_ADDRESS,
            active=False,  # Inactive chain to check handling of non-active chains in Service Mgr
        ),
    ]


@pytest.fixture
def mock_registry(mock_chains: List[Chain]) -> ChainRegistry:
    """Create a mock registry with test chains."""
    registry = ChainRegistry()
    registry.chains = mock_chains
    for chain in mock_chains:
        registry.chain_by_id[chain.id] = chain
    return registry


@pytest.fixture
async def service_manager(mock_registry: ChainRegistry) -> ChainServiceMgr:
    """Create a ChainServiceMgr instance with mocked registry."""
    return ChainServiceMgr(mock_registry, MarketState())


@pytest.mark.asyncio
async def test_chainservice_mgr_init(mock_registry: ChainRegistry):
    """Test ChainServiceMgr initialization."""
    manager = ChainServiceMgr(mock_registry, MarketState())

    assert len(manager.services) == len(mock_registry.chains) - 1  # Exclude inactive chain
    assert manager.chain_registry == mock_registry

    service = manager.services[0]
    assert service.chain == mock_registry.chains[0]
    assert not service.is_running
    assert service.mgr == manager


@pytest.mark.asyncio
async def test_chainservice_mgr_run(service_manager: ChainServiceMgr):
    """Test running all chain services."""
    start_mock = AsyncMock()
    with patch("app.evm.service.ChainService.start", start_mock):
        await service_manager.run()
        # Verify start was called for each service
        assert start_mock.call_count == len(service_manager.services)


@pytest.mark.asyncio
async def test_chainservice_mgr_shutdown(service_manager: ChainServiceMgr):
    """Test shutting down all chain services."""
    stop_mock = AsyncMock()
    with patch("app.evm.service.ChainService.stop", stop_mock):
        for service in service_manager.services:
            service.is_running = True

        # Shutdown services
        await service_manager.shutdown()

        # Verify stop was called for each service
        assert stop_mock.call_count == len(service_manager.services)

        # Verify services are marked as not running
        assert all(not service.is_running for service in service_manager.services)


@pytest.mark.asyncio
async def test_chainservice_mgr_run_already_running(service_manager: ChainServiceMgr):
    """Test running services that are already running."""
    start_mock = AsyncMock()
    with patch("app.evm.service.ChainService.start", start_mock):
        # Mark services as already running
        for service in service_manager.services:
            service.is_running = True

        await service_manager.run()
        # Verify start was not called since services were already running
        assert start_mock.call_count == 0


@pytest.mark.asyncio
async def test_chainservice_mgr_shutdown_not_running(service_manager: ChainServiceMgr):
    """Test shutting down services that are not running."""
    stop_mock = AsyncMock()
    with patch("app.evm.service.ChainService.stop", stop_mock):
        # Mark services as not running
        for service in service_manager.services:
            service.is_running = False
        # Attempt to shutdown services
        await service_manager.shutdown()

        # Verify stop was not called since services were not running
        assert stop_mock.call_count == 0

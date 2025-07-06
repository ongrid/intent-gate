"""Tests for ChainRegistry class."""

import os
from unittest.mock import patch

import pytest

from app.evm.registry import ChainRegistry
from app.schemas.token import ERC20Token

ENVS = {
    "ETH_WS_URL": "wss://eth.example.com",
    "BASE_WS_URL": "wss://base.example.com",
    "ARB_WS_URL": "ws://arbitrum.example.com",
}


@pytest.fixture
def registry_from_inventory() -> ChainRegistry:
    return ChainRegistry.from_chains_inventory()


def test_registry_with_data(registry_from_inventory: ChainRegistry):
    """Test ChainRegistry initializes empty."""
    assert isinstance(registry_from_inventory, ChainRegistry)
    assert len(registry_from_inventory.chains) > 0
    assert len(registry_from_inventory.chain_by_id) > 0
    assert registry_from_inventory.chain_by_id[1].id == 1
    assert registry_from_inventory.chain_by_id[8453].id == 8453
    assert registry_from_inventory.chain_by_id[42161].id == 42161
    assert len(registry_from_inventory.token_by_chain_id_and_address) > 0
    token = registry_from_inventory.token_by_chain_id_and_address[
        (1, "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    ]
    assert isinstance(token, ERC20Token)
    assert token.name == "Wrapped Ether"
    assert token.symbol == "WETH"
    assert token.chain.id == 1
    assert token.address == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"


def test_get_chain_by_id(registry_from_inventory: ChainRegistry):
    """Test getting chain by ID."""
    # Test existing chain
    chain = registry_from_inventory.get_chain_by_id(1)
    assert chain is not None
    assert chain.id == 1
    assert chain.name == "Ethereum"
    assert chain.short_names == ["eth", "ethereum"]
    assert chain.gas_token == "ETH"
    assert chain.poa is False

    # Test non-existent chain
    assert registry_from_inventory.get_chain_by_id(999) is None


def test_get_token_by_chain_id_and_address(registry_from_inventory: ChainRegistry):
    """Test getting token by chain ID and address."""
    # Test existing token
    token = registry_from_inventory.get_token_by_chain_id_and_address(
        8453, "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c"
    )
    assert token is not None
    assert isinstance(token, ERC20Token)
    assert token.name == "Wrapped BTC"
    assert token.symbol == "WBTC"
    assert token.chain.id == 8453
    assert token.address == "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c"
    assert token.decimals == 8

    # Test non-existent token
    assert (
        registry_from_inventory.get_token_by_chain_id_and_address(
            1, "0x0000000000000000000000000000000000000000"
        )
        is None
    )

    # Test non-existent chain ID
    assert (
        registry_from_inventory.get_token_by_chain_id_and_address(
            999, "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        )
        is None
    )

    # Test case-insensitive address
    token = registry_from_inventory.get_token_by_chain_id_and_address(
        42161, "0xaf88d065e77c8cC2239327C5EDb3A432268e5831".lower()
    )
    assert token is not None
    assert token.name == "Arbitrum USDC"


def test_from_env_valid_ws_urls(registry_from_inventory: ChainRegistry):
    """Test loading valid WebSocket URLs from environment for multiple chains."""
    # Check initial state
    eth_chain = registry_from_inventory.get_chain_by_id(1)
    base_chain = registry_from_inventory.get_chain_by_id(8453)
    arb_chain = registry_from_inventory.get_chain_by_id(42161)
    assert eth_chain is not None
    assert base_chain is not None
    assert arb_chain is not None
    assert eth_chain.ws_rpc_url is None
    assert base_chain.ws_rpc_url is None
    assert arb_chain.ws_rpc_url is None

    with patch.dict(os.environ, ENVS):
        registry_from_inventory.from_env()
        assert eth_chain.ws_rpc_url == "wss://eth.example.com"
        assert eth_chain.active is True
        assert base_chain.ws_rpc_url == "wss://base.example.com"
        assert base_chain.active is True
        assert arb_chain.ws_rpc_url == "ws://arbitrum.example.com"
        assert arb_chain.active is True


def test_from_env_inactive_when_missing_ws_urls(registry_from_inventory: ChainRegistry):
    """Test chains are inactive when WebSocket URLs are missing."""
    PARTIALLY_MISSING_ENVS = ENVS.copy()
    del PARTIALLY_MISSING_ENVS["ETH_WS_URL"]
    with patch.dict(os.environ, PARTIALLY_MISSING_ENVS, clear=True):
        registry_from_inventory.from_env()
        eth_chain = registry_from_inventory.get_chain_by_id(1)
        assert eth_chain is not None
        assert eth_chain.ws_rpc_url == ""  # Should be empty if not set
        assert eth_chain.active is False  # Chain should be inactive if no URL set
        base_chain = registry_from_inventory.get_chain_by_id(8453)
        assert base_chain is not None
        assert base_chain.ws_rpc_url == "wss://base.example.com"
        assert base_chain.active is True
        arb_chain = registry_from_inventory.get_chain_by_id(42161)
        assert arb_chain is not None
        assert arb_chain.ws_rpc_url == "ws://arbitrum.example.com"


def test_from_env_invalid_ws_urls(registry_from_inventory: ChainRegistry):
    """Test loading invalid WebSocket URL from environment."""
    INCORRECT_ENVS = ENVS.copy()
    INCORRECT_ENVS["ETH_WS_URL"] = "http://eth.example.com"  # Invalid URL scheme
    with patch.dict(os.environ, INCORRECT_ENVS):
        with pytest.raises(ValueError, match="Invalid WebSocket URL"):
            registry_from_inventory.from_env()
    INCORRECT_ENVS["ETH_WS_URL"] = "invalid_&:url"  # Invalid URL format
    with patch.dict(os.environ, INCORRECT_ENVS):
        with pytest.raises(ValueError, match="Invalid WebSocket URL"):
            registry_from_inventory.from_env()


def test_from_env_empty_registry():
    """Test error when calling from_env on empty registry."""
    registry = ChainRegistry()
    with pytest.raises(AssertionError, match="must be initialized with chains"):
        registry.from_env()

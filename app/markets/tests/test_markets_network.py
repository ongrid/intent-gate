import pytest

from app.evm.chains import arbitrum, ethereum
from app.markets.markets import MarketState


@pytest.fixture
def market_state():
    return MarketState()


def test_arbitrum_stablecoins_connected(market_state):
    for a, b in [
        (arbitrum.USDT, arbitrum.USDC),
        (arbitrum.USDT, arbitrum.DAI),
        (arbitrum.USDC, arbitrum.DAI),
    ]:
        assert market_state.graph.has_edge(a, b)
        assert market_state.graph[a][b]["weight"] == 1.0


def test_ethereum_stablecoins_connected(market_state):
    for a, b in [
        (ethereum.USDT, ethereum.USDC),
        (ethereum.USDT, ethereum.DAI),
        (ethereum.USDC, ethereum.DAI),
    ]:
        assert market_state.graph.has_edge(a, b)
        assert market_state.graph[a][b]["weight"] == 1.0


def test_cross_chain_disconnected(market_state):
    assert not market_state.graph.has_edge(arbitrum.USDT, ethereum.USDT)

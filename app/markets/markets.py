from typing import Generator

import networkx as nx

from app.evm.chains import arbitrum, ethereum
from app.schemas.token import ERC20Token


class MarketState:  # pylint: disable=too-few-public-methods
    """Singleton class to hold the market state (prices) graph"""

    graph: nx.Graph

    def __init__(self) -> None:
        """Initialize a trivial single-weighted graph for stablecoin swaps 1:1"""
        self.graph = nx.Graph()
        self.graph.add_edge(arbitrum.USDT, arbitrum.USDC, weight=1.0)
        self.graph.add_edge(arbitrum.USDC, arbitrum.USDT, weight=1.0)
        self.graph.add_edge(arbitrum.USDT, arbitrum.DAI, weight=1.0)
        self.graph.add_edge(arbitrum.DAI, arbitrum.USDT, weight=1.0)
        self.graph.add_edge(arbitrum.USDC, arbitrum.DAI, weight=1.0)
        self.graph.add_edge(arbitrum.DAI, arbitrum.USDC, weight=1.0)
        self.graph.add_edge(ethereum.USDT, ethereum.USDC, weight=1.0)
        self.graph.add_edge(ethereum.USDC, ethereum.USDT, weight=1.0)
        self.graph.add_edge(ethereum.USDT, ethereum.DAI, weight=1.0)
        self.graph.add_edge(ethereum.DAI, ethereum.USDT, weight=1.0)
        self.graph.add_edge(ethereum.USDC, ethereum.DAI, weight=1.0)
        self.graph.add_edge(ethereum.DAI, ethereum.USDC, weight=1.0)

    def get_tokens_by_chain_id(self, chain_id: int) -> Generator[ERC20Token, None, None]:
        """Generator that yields all tokens for a specific chain."""
        for node in self.graph.nodes():
            if isinstance(node, ERC20Token) and node.chain.id == chain_id:
                yield node

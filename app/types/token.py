"""ERC-20 token related classes and schemas."""

from dataclasses import dataclass

from .chain import Chain


@dataclass
class ERC20Token:
    """Represents an ERC20 token with its chain and contract details."""

    name: str
    symbol: str
    chain: Chain
    address: str
    decimals: int = 18

"""ERC-20 token related classes and schemas."""

from dataclasses import dataclass
from typing import Any

from eth_typing import ChecksumAddress

from .chain import Chain


@dataclass(frozen=True)
class ERC20Token:
    """Represents an ERC20 token with its chain and contract details."""

    name: str
    symbol: str
    chain: Chain
    address: ChecksumAddress
    decimals: int = 18

    def __hash__(self) -> int:
        """Hash based on chain and address which uniquely identify a token.
        for use in hash-based collection like networkx graphs.
        """
        return hash((self.chain.id, self.address.lower()))

    def __eq__(self, other: Any) -> bool:
        """Compare tokens based on chain and normalized address."""
        if not isinstance(other, ERC20Token):
            return NotImplemented
        return self.chain == other.chain and self.address.lower() == other.address.lower()

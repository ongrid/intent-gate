"""ERC-20 token related classes and schemas."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Union

from eth_typing import ChecksumAddress

from .chain import Chain


@dataclass
class ERC20Token:
    """Represents an ERC20 token with its chain and contract details."""

    name: str
    symbol: str
    chain: Chain
    address: ChecksumAddress
    decimals: int = 18
    # Updated by ERC20Service
    raw_balance: int = 0
    last_updated_block: int = 0

    def raw_to_decimal(self, raw_amount: int) -> Decimal:
        """Convert raw token amount to decimal representation.

        Args:
            raw_amount: Raw token amount (wei-like units)

        Returns:
            Decimal representation of the amount

        Example:
            >>> token = ERC20Token(decimals=18, ...)
            >>> token.raw_to_decimal(1000000000000000000)
            Decimal('1.0')
        """
        return Decimal(raw_amount) / Decimal(10**self.decimals)

    def decimal_to_raw(self, decimal_amount: Union[str, int, float, Decimal]) -> int:
        """Convert decimal amount to raw token amount.

        Args:
            decimal_amount: Decimal representation of the amount

        Returns:
            Raw token amount (wei-like units)

        Example:
            >>> token = ERC20Token(decimals=18, ...)
            >>> token.decimal_to_raw('1.5')
            1500000000000000000
        """
        return int(Decimal(str(decimal_amount)) * Decimal(10**self.decimals))

    @property
    def balance(self) -> Decimal:
        """Get current balance as decimal amount."""
        return self.raw_to_decimal(self.raw_balance)

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

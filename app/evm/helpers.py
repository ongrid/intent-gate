"""Helper functions for EVM-related operations."""

from eth_typing import HexStr
from web3 import Web3


def encode_address(address: str) -> HexStr:
    """Pad address to 32 bytes for topic filtering."""
    if not Web3.is_checksum_address(address):
        raise ValueError(f"Address not checksummed: {address}")
    return Web3.to_hex(Web3().codec.encode(["address"], [address]))

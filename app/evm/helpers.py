"""Helper functions for EVM-related operations."""

from uuid import UUID

from eth_hash.auto import keccak
from eth_typing import HexStr
from hexbytes import HexBytes
from web3 import Web3


def encode_address(address: str) -> HexStr:
    """Pad address to 32 bytes for topic filtering."""
    if not Web3.is_checksum_address(address):
        raise ValueError(f"Address not checksummed: {address}")
    return Web3.to_hex(Web3().codec.encode(["address"], [address]))


def uuid_to_topic(rfq_id: UUID) -> HexBytes:
    """Convert a UUID to a keccak256 topic hash for event filtering.

    Args:
        rfq_id: UUID object to convert to topic hash

    Returns:
        HexBytes: 32-byte keccak256 hash as HexBytes, compatible with log receipt topics"""

    return HexBytes(keccak(str(rfq_id).encode("utf-8")))

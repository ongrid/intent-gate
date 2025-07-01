from dataclasses import dataclass

from eth_abi import encode
from eth_typing import Hash32
from eth_utils import keccak, to_checksum_address

EIP712_DOMAIN_TYPEHASH = keccak(
    text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
)
SINGLE_ORDER_TYPEHASH = keccak(
    text="Single(string,uint256,address,address,address,address,uint256,uint256,uint256,uint256,address)"
)
DOMAIN_NAME = keccak(text="LiquoriceSettlement")
DOMAIN_VERSION = keccak(text="1")
EIP191_HEADER = b"\x19\x01"
LIQUORICE_SETTLEMENT_CONTRACT = "0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167"


@dataclass(frozen=True)
class SignableRfqQuoteLevel:
    """EIP-712 signable order structure combining RFQ and quote level data."""

    base_token: str
    base_token_amount: str
    chain_id: int
    settlement_contract: str
    effective_trader: str
    quote_expiry: int
    min_quote_token_amount: str
    nonce: str
    quote_token: str
    quote_token_amount: str
    recipient: str
    rfq_id: str
    market: str
    trader: str

    @property
    def _domain_separator(self) -> Hash32:
        """Generate the EIP-712 domain separator for the RFQ quote level."""
        return Hash32(
            keccak(
                encode(
                    ["bytes32", "bytes32", "bytes32", "uint256", "address"],
                    [
                        EIP712_DOMAIN_TYPEHASH,
                        DOMAIN_NAME,
                        DOMAIN_VERSION,
                        self.chain_id,
                        self.settlement_contract,
                    ],
                )
            )
        )

    @property
    def _struct_hash(self) -> Hash32:
        rfq_id_hash = keccak(encode(["string"], [str(self.rfq_id)]))
        return Hash32(
            keccak(
                encode(
                    [
                        "bytes32",
                        "bytes32",
                        "uint256",
                        "address",
                        "address",
                        "address",
                        "address",
                        "uint256",
                        "uint256",
                        "uint256",
                        "uint256",
                        "address",
                    ],
                    [
                        SINGLE_ORDER_TYPEHASH,
                        rfq_id_hash,
                        int(self.nonce, 16),
                        to_checksum_address(self.trader),
                        to_checksum_address(self.effective_trader),
                        to_checksum_address(self.base_token),
                        to_checksum_address(self.quote_token),
                        int(self.base_token_amount),
                        int(self.quote_token_amount),
                        int(self.min_quote_token_amount),
                        int(self.quote_expiry),
                        to_checksum_address(self.recipient),
                    ],
                )
            )
        )

    @property
    def hash(self) -> Hash32:
        """Generate the full EIP-712 digest for the RFQ quote level."""
        return Hash32(keccak(EIP191_HEADER + self._domain_separator + self._struct_hash))

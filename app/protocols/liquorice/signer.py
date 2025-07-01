from dataclasses import dataclass
from uuid import UUID

from eth_abi import encode
from eth_account.signers.local import LocalAccount
from eth_typing import Hash32, HexStr
from eth_utils import keccak, to_checksum_address
from hexbytes import HexBytes
from web3 import Web3

from .schemas import RFQQuoteMessage

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


@dataclass(frozen=False)
class SignableRfqQuoteLevel:
    """EIP-712 signable order structure combining RFQ and quote level data."""

    base_token: str
    base_token_amount: int
    chain_id: int
    settlement_contract: str
    effective_trader: str
    quote_expiry: int
    min_quote_token_amount: int
    nonce: HexBytes
    quote_token: str
    quote_token_amount: int
    recipient: str
    rfq_id: UUID
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
                        int.from_bytes(self.nonce, byteorder="big"),
                        to_checksum_address(self.trader),
                        to_checksum_address(self.effective_trader),
                        to_checksum_address(self.base_token),
                        to_checksum_address(self.quote_token),
                        self.base_token_amount,
                        self.quote_token_amount,
                        self.min_quote_token_amount,
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


class Web3Signer:
    def __init__(self, priv_key: HexStr):
        self.account: LocalAccount = Web3().eth.account.from_key(priv_key)

    def sign_quote_levels(self, quote: RFQQuoteMessage) -> RFQQuoteMessage:
        for quote_level in quote.levels:
            quote_level.recipient = self.account.address
            quote_level.signer = self.account.address
            signable_lvl = SignableRfqQuoteLevel(
                base_token=quote_level.baseToken,
                base_token_amount=quote_level.baseTokenAmount,
                chain_id=quote._rfq.chainId,
                effective_trader=quote._rfq.effectiveTrader,
                quote_expiry=quote_level.expiry,
                min_quote_token_amount=quote_level.minQuoteTokenAmount,
                nonce=quote._rfq.nonce,
                quote_token=quote_level.quoteToken,
                quote_token_amount=quote_level.quoteTokenAmount,
                recipient=quote_level.recipient,
                rfq_id=quote.rfqId,
                market=quote_level.settlementContract,
                trader=quote._rfq.trader,
                settlement_contract=LIQUORICE_SETTLEMENT_CONTRACT,
            )
            quote_level.signature = self.account.unsafe_sign_hash(signable_lvl.hash).signature

        return quote

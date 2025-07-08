import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from eth_abi import encode
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress, Hash32, HexStr
from eth_utils import keccak, to_checksum_address
from hexbytes import HexBytes
from web3 import Web3

from app.evm.registry import ChainRegistry

from .schemas import RFQMessage, RFQQuoteMessage

EIP712_DOMAIN_TYPEHASH = keccak(
    text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
)
SINGLE_ORDER_TYPEHASH = keccak(
    text="Single(string,uint256,address,address,address,address,uint256,uint256,uint256,uint256,address)"
)
DOMAIN_NAME = keccak(text="LiquoriceSettlement")
DOMAIN_VERSION = keccak(text="1")
EIP191_HEADER = b"\x19\x01"

log = logging.getLogger(__name__)


@dataclass(frozen=False)
class SignableRfqQuoteLevel:
    """EIP-712 signable order structure combining RFQ and quote level data."""

    base_token: ChecksumAddress
    base_token_amount: int
    chain_id: int
    settlement_contract: ChecksumAddress
    effective_trader: ChecksumAddress
    quote_expiry: int
    min_quote_token_amount: int
    nonce: HexBytes
    quote_token: ChecksumAddress
    quote_token_amount: int
    recipient: ChecksumAddress
    rfq_id: UUID
    market: ChecksumAddress
    trader: ChecksumAddress

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
    """Singleton signer configured with a private key and chain registry access.
    Signs RFQ quote levels by applying chain-specific attributes and generating EIP-712 signatures.
    Validates chain existence and active status before signing quote levels."""

    account: LocalAccount
    chain_registry: ChainRegistry

    def __init__(self, chain_registry: ChainRegistry, priv_key: HexStr):
        self.account = Web3().eth.account.from_key(priv_key)
        self.chain_registry = chain_registry

    def sign_quote_levels(
        self, rfq: RFQMessage, quote: RFQQuoteMessage
    ) -> Optional[RFQQuoteMessage]:
        """Sign RFQ quote levels with the account's private key."""
        chain_id = rfq.chainId
        if chain_id not in self.chain_registry.chain_by_id:
            log.error("Chain ID %s not found in chain registry", chain_id)
            return None
        chain = self.chain_registry.chain_by_id[chain_id]
        if not chain.active:
            log.error("Chain %s is not active", chain.name)
            return None
        assert chain.skeeper_address
        assert chain.liquorice_settlement_address
        for quote_level in quote.levels:
            quote_level.recipient = self.account.address
            quote_level.signer = self.account.address
            signable_lvl = SignableRfqQuoteLevel(
                base_token=quote_level.baseToken,
                base_token_amount=quote_level.baseTokenAmount,
                chain_id=rfq.chainId,
                effective_trader=rfq.effectiveTrader,
                quote_expiry=quote_level.expiry,
                min_quote_token_amount=quote_level.minQuoteTokenAmount,
                nonce=rfq.nonce,
                quote_token=quote_level.quoteToken,
                quote_token_amount=quote_level.quoteTokenAmount,
                # Both recipient and EIP-1271 verifier are same if you use SKeeper contract address
                recipient=chain.skeeper_address,
                rfq_id=quote.rfqId,
                market=quote_level.settlementContract,
                trader=rfq.trader,
                settlement_contract=chain.liquorice_settlement_address,
            )
            quote_level.signature = self.account.unsafe_sign_hash(signable_lvl.hash).signature
            # Both recipient and EIP-1271 verifier are same if you use SKeeper contract address
            quote_level.eip1271Verifier = chain.skeeper_address
            quote_level.recipient = chain.skeeper_address
            quote_level.signer = self.account.address
            quote_level.settlementContract = chain.liquorice_settlement_address

        return quote

import re
from enum import Enum
from typing import (
    Annotated,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)
from web3 import Web3

MAX_UINT256 = 2**256 - 1


class MessageType(str, Enum):
    RFQ = "rfq"
    RFQ_QUOTE = "rfqQuote"
    UNKNOWN = "unknown"


class IntentMetadataContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    auctionId: int  # CoW auction ID


class IntentMetadata(BaseModel):
    """For the moment, only CoW Protocol is supported. If this parameter is absent,
    it means that the quote is requested for another intent system.
    """

    model_config = ConfigDict(frozen=True)

    source: Literal["cow_protocol"]
    content: IntentMetadataContent


class RFQMessage(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )
    chainId: int
    solver: Annotated[Optional[str], Field(description="Name of the solver requesting the quote")]
    solverRfqId: Annotated[UUID, Field(description="UUID of the originating solver RFQ")]
    rfqId: Annotated[UUID, Field(description="UUID of the RFQ")]
    nonce: Annotated[
        HexBytes,
        Field(description="Single-use number assigned by liquorice to avoid replay attacks"),
    ]
    baseToken: Annotated[
        ChecksumAddress, Field(description="Address of token to be sent by trader")
    ]
    quoteToken: Annotated[
        ChecksumAddress, Field(description="Address of the token to be received by trader")
    ]
    trader: Annotated[
        ChecksumAddress, Field(description="Address of the account sending baseToken")
    ]
    effectiveTrader: Annotated[
        ChecksumAddress,
        Field(description="Effective trader address, can be different from trader"),
    ]
    expiry: Annotated[int, Field(description="UNIX timestamp (seconds) when the RFQ expires")]
    baseTokenAmount: Annotated[
        Optional[int],
        Field(
            description="Amount of baseToken with up to 18 decimal places, e.g. 100000000 (1 WBTC)"
        ),
    ] = None
    quoteTokenAmount: Annotated[
        Optional[int],
        Field(
            description="Amount of quoteToken with up to 18 decimal places, e.g. 100000000 (1 WBTC)"
        ),
    ] = None
    intentMetadata: Annotated[
        Optional[IntentMetadata], Field(description="Additional info about intent source")
    ] = None

    @field_validator("expiry", mode="before")
    @classmethod
    def validate_expiry(cls, v: int) -> int:
        """Validate expiry is a positive integer."""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("Expiry must be a positive integer (UNIX timestamp in seconds)")
        if not 1750000000 < v < 2000000000:  # Reasonable range for future timestamps
            raise ValueError("Expiry must be a unix timestamp in seconds")
        return v

    @field_validator("baseTokenAmount", "quoteTokenAmount", mode="before")
    @classmethod
    def validate_token_amount(cls, v: Optional[Union[str, int]]) -> Optional[int]:
        """Validate token amount is a decimal integer string."""
        if v is None:
            return v

        if isinstance(v, str):
            # Check it's a valid decimal string
            if not re.match(r"^\d+$", v):
                raise ValueError("Amount must be a string containing only digits")

            # Check length doesn't exceed 256 bits (78 decimal digits)
            if len(v) > len(str(MAX_UINT256)):
                raise ValueError("Amount exceeds maximum token value (256 bits)")

            # Verify it parses to a non-negative integer
            try:
                amount = int(v)
            except ValueError:
                raise ValueError("Non-integer value")

            if amount < 0:
                raise ValueError("Amount must be non-negative")

            return amount

        elif isinstance(v, int):
            # If it's already an integer, just validate it
            if v < 0:
                raise ValueError("Amount must be non-negative")
            if v > MAX_UINT256:
                raise ValueError("Amount exceeds maximum token value (256 bits)")
            return v

        raise ValueError("Amount must be an integer or string")

    @field_validator("nonce", mode="before")
    @classmethod
    def validate_and_convert_nonce(cls, v: Union[str, HexBytes]) -> HexBytes:
        if isinstance(v, HexBytes):
            if len(v) != 32:
                raise ValueError("nonce must be a 32-byte hex string")
            return v
        if isinstance(v, str):
            if v.startswith("0x"):
                v = v[2:]
            if not re.match(r"^[0-9a-f]{64}$", v):
                raise ValueError("nonce must be a 32-byte hex string")
            return HexBytes(v)

    @field_validator("baseToken", "quoteToken", "trader", "effectiveTrader")
    @classmethod
    def validate_and_convert_address(cls, v: str) -> ChecksumAddress:
        """Convert and validate Ethereum address to checksum format."""
        if not Web3.is_address(v):
            raise ValueError("Bad Ethereum address")
        if not Web3.is_checksum_address(v):
            raise ValueError("Bad Ethereum checksum")
        return Web3.to_checksum_address(v)

    @model_validator(mode="after")
    def check_exactly_one_amount(self) -> "RFQMessage":
        """
        Validates that exactly one of `baseTokenAmount` or `quoteTokenAmount` is provided.

        - If `baseTokenAmount` is specified: the trader wants to know how much quoteToken they'd receive for a given amount of baseToken.
        - If `quoteTokenAmount` is specified: the trader wants to know how much baseToken they must provide to receive a specific amount of quoteToken.
        """
        if bool(self.baseTokenAmount) == bool(self.quoteTokenAmount):
            raise ValueError("Exactly one of baseTokenAmount or quoteTokenAmount must be set")
        return self

    def model_dump(self, *args, **kwargs):
        raise NotImplementedError("Serialization is not supported")

    def model_dump_json(self, *args, **kwargs):
        raise NotImplementedError("JSON serialization is not supported")


class QuoteLevelLite(BaseModel):
    """
    Quote level Lite
    Use this type of quote level for simple and gas-efficient swaps.

    Notes:
    - Only standard approvals are supported.
    - Quoted amounts must not exceed those specified in the RFQ.
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )
    type: Literal["lite"] = "lite"
    expiry: Annotated[int, Field(description="UNIX timestamp (seconds) when the Quote expires")]
    settlementContract: Annotated[
        ChecksumAddress, Field(description="Address of the settlement contract")
    ]
    signer: Annotated[ChecksumAddress, Field(description="Address of the signer of the quote")]
    recipient: Annotated[
        Optional[ChecksumAddress], Field(description="Recipient of the funds")
    ] = None
    baseToken: Annotated[
        ChecksumAddress, Field(description="Address of token to be sent by trader")
    ]
    quoteToken: Annotated[
        ChecksumAddress, Field(description="Address of the token to be received by trader")
    ]
    baseTokenAmount: Annotated[
        int,
        Field(
            description="Amount of baseToken with up to 18 decimal places, e.g. 100000000 (1 WBTC)"
        ),
    ]
    quoteTokenAmount: Annotated[
        int,
        Field(
            description="Amount of quoteToken with up to 18 decimal places, e.g. 100000000 (1 WBTC)"
        ),
    ]
    minQuoteTokenAmount: Annotated[
        int,
        Field(description="Minimum amount of quoteToken to receive for partial fills"),
    ]
    signature: Annotated[
        HexBytes,
        Field(description="Signature for this quote level"),
    ]

    @field_validator("signature", mode="before")
    @classmethod
    def validate_signature(cls, v: str | bytes | HexBytes) -> HexBytes:
        """Convert signature to HexBytes."""
        if isinstance(v, (bytes, HexBytes)):
            return HexBytes(v)
        if isinstance(v, str):
            if not v.startswith("0x"):
                v = "0x" + v
            return HexBytes(v)
        raise ValueError("signature must be bytes or hex string")

    @field_serializer("signature")
    def serialize_signature(self, v: HexBytes, _info):
        """Serialize HexBytes signature to 0x-prefixed hex string."""
        return "0x" + v.hex()


class RFQQuoteMessage(BaseModel):
    """Market makers can provide multiple quote levels with different amounts,
    but the quoted amounts must not exceed those in the RFQ.
    """

    model_config = ConfigDict(frozen=True)
    rfqId: UUID
    levels: List[QuoteLevelLite]  # extend this if other level types are added


T = TypeVar("T", RFQMessage, RFQQuoteMessage)


class LiquoriceEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True, revalidate_instances="always")

    messageType: MessageType = MessageType.UNKNOWN
    message: T

    @model_validator(mode="before")
    @classmethod
    def infer_message_type(cls, values: dict) -> dict:
        if "messageType" not in values:
            msg = values.get("message")
            if isinstance(msg, RFQMessage):
                values["messageType"] = MessageType.RFQ
            elif isinstance(msg, RFQQuoteMessage):
                values["messageType"] = MessageType.RFQ_QUOTE
        return values

    @model_validator(mode="after")
    def validate_message_type_consistency(self) -> "LiquoriceEnvelope[T]":
        msg_class_map: Dict[MessageType, Type[BaseModel]] = {
            MessageType.RFQ: RFQMessage,
            MessageType.RFQ_QUOTE: RFQQuoteMessage,
        }
        expected_cls = msg_class_map.get(self.messageType)
        if expected_cls and not isinstance(self.message, expected_cls):
            raise ValueError(
                f"Message type mismatch: {self.messageType.value} requires {expected_cls.__name__}, "
                f"got {type(self.message).__name__}"
            )
        if self.messageType == MessageType.UNKNOWN:
            raise ValueError("Unknown message type, cannot infer message type from content")
        return self

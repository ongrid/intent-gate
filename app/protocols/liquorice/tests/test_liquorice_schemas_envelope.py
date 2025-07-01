import json
from pathlib import Path
from uuid import UUID

import pytest
from hexbytes import HexBytes
from web3 import Web3

from app.protocols.liquorice.schemas import (
    IntentMetadata,
    IntentMetadataContent,
    LiquoriceEnvelope,
    MessageType,
    QuoteLevelLite,
    RFQMessage,
    RFQQuoteMessage,
)

EXAMPLE_RFQ_MESSAGE_DICT = json.loads(
    (Path(__file__).parent / "data" / "liquorice_rfq.json").read_text()
)


def test_envelope_init_infer_quote_type():
    levels = []
    levels.append(
        QuoteLevelLite(
            expiry=1746972086,
            settlementContract=Web3.to_checksum_address(
                "0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167"
            ),
            recipient=Web3.to_checksum_address("0xB073C430FbDd0f56D6BfDdcb7e40C17CC611Fc04"),
            signer=Web3.to_checksum_address("0xB073C430FbDd0f56D6BfDdcb7e40C17CC611Fc04"),
            baseToken=Web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"),
            quoteToken=Web3.to_checksum_address("0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
            baseTokenAmount=1249771130,
            quoteTokenAmount=135542446,
            minQuoteTokenAmount=1,
            signature=HexBytes(
                "0xa235ba3136acb14c5968f119af99983b0af5ea42349ec4f891c4f48ed97c3c6b43ef48ec75875c5400461bdaea02619e6db8e2b2c0daf5f15b5280c0d4067c571b"
            ),
        )
    )
    quote_lite_msg = RFQQuoteMessage(
        rfqId=UUID("2aca5f16-defd-4f0c-9d4e-f219d69cbd7b"),
        levels=levels,
        _rfq=RFQMessage(**EXAMPLE_RFQ_MESSAGE_DICT["message"]),
    )
    quote_envelope = LiquoriceEnvelope(message=quote_lite_msg)
    assert quote_envelope.messageType == "rfqQuote"


def test_envelope_init_infer_rfq_type():
    intent_meta = IntentMetadata(
        source="cow_protocol", content=IntentMetadataContent(auctionId=3824359)
    )
    rfq_msg = RFQMessage(
        chainId=42161,
        solver="portus",
        solverRfqId=UUID("95a0f428-a6c4-4207-81b2-e47436741e9b"),
        rfqId=UUID("846063db-1769-438b-8002-00fd981603df"),
        nonce=HexBytes("0xade8af8413607c37361fcebe3b00cc3de354986c188efe9d6db0fa8c74843ad0"),
        expiry=1750707521,
        baseToken=Web3.to_checksum_address("0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
        quoteToken=Web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"),
        trader=Web3.to_checksum_address("0x9008D19f58AAbD9eD0D60971565AA8510560ab41"),
        effectiveTrader=Web3.to_checksum_address("0x9008D19f58AAbD9eD0D60971565AA8510560ab41"),
        baseTokenAmount=6358600000,  # using int for baseTokenAmount
        quoteTokenAmount=None,
        intentMetadata=intent_meta,
    )
    rfq_envelope = LiquoriceEnvelope(message=rfq_msg)
    assert rfq_envelope.messageType == "rfq"


def test_envelope_init_raise_when_inconsistent_types():
    """Test that LiquoriceEnvelope raises an error when messageType does not match message type."""
    with pytest.raises(ValueError, match="Message type mismatch"):
        LiquoriceEnvelope(
            message=RFQQuoteMessage(
                rfqId=UUID("2aca5f16-defd-4f0c-9d4e-f219d69cbd7b"),
                levels=[],
                _rfq=RFQMessage(**EXAMPLE_RFQ_MESSAGE_DICT["message"]),
            ),
            messageType=MessageType.RFQ,
        )


def test_envelope_init_infer_raise_when_unknown_type():
    """Test that LiquoriceEnvelope raises an error when messageType is unknown"""
    with pytest.raises(ValueError, match="validation error"):
        LiquoriceEnvelope(message=IntentMetadataContent(auctionId=0))  # type: ignore[type-var]
    with pytest.raises(ValueError, match="Unknown message type, cannot infer message type"):
        LiquoriceEnvelope(
            message=RFQQuoteMessage(
                rfqId=UUID("2aca5f16-defd-4f0c-9d4e-f219d69cbd7b"),
                levels=[],
                _rfq=RFQMessage(**EXAMPLE_RFQ_MESSAGE_DICT["message"]),
            ),
            messageType=MessageType.UNKNOWN,
        )

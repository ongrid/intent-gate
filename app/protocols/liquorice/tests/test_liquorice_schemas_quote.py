import json
from pathlib import Path
from uuid import UUID

import pytest
from hexbytes import HexBytes
from web3 import Web3

from app.protocols.liquorice.schemas import (
    LiquoriceEnvelope,
    MessageType,
    QuoteLevelLite,
    RFQQuoteMessage,
)

valid_quote_lite_envelope_text = (
    Path(__file__).parent / "data" / "liquorice_quote_lite.json"
).read_text()
valid_quote_lite_envelope_json = json.loads(valid_quote_lite_envelope_text)


def test_parse_valid_quote_lite_from_live_data():
    quote_lite_msg_dict = valid_quote_lite_envelope_json["message"]
    quote_lite_msg = RFQQuoteMessage.model_validate_json(json.dumps(quote_lite_msg_dict))
    assert quote_lite_msg.rfqId == UUID("2aca5f16-defd-4f0c-9d4e-f219d69cbd7b")
    assert quote_lite_msg.levels[0].expiry == 1746972086
    assert (
        quote_lite_msg.levels[0].settlementContract == "0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167"
    )
    assert quote_lite_msg.levels[0].recipient == "0xB073C430FbDd0f56D6BfDdcb7e40C17CC611Fc04"
    assert quote_lite_msg.levels[0].signer == "0xB073C430FbDd0f56D6BfDdcb7e40C17CC611Fc04"
    assert quote_lite_msg.levels[0].baseToken == "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    assert quote_lite_msg.levels[0].quoteToken == "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    assert quote_lite_msg.levels[0].baseTokenAmount == 1249771130
    assert quote_lite_msg.levels[0].quoteTokenAmount == 135542446
    assert quote_lite_msg.levels[0].minQuoteTokenAmount == 1
    assert quote_lite_msg.levels[0].signature == HexBytes(
        "0xa235ba3136acb14c5968f119af99983b0af5ea42349ec4f891c4f48ed97c3c6b43ef48ec75875c5400461bdaea02619e6db8e2b2c0daf5f15b5280c0d4067c571b"
    )
    assert quote_lite_msg.levels[0].type == "lite"


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
        rfqId=UUID("2aca5f16-defd-4f0c-9d4e-f219d69cbd7b"), levels=levels
    )
    quote_envelope = LiquoriceEnvelope(message=quote_lite_msg)
    assert quote_envelope.messageType == "rfqQuote"


def test_envelope_init_when_inconsistent_types():
    """Test that LiquoriceEnvelope raises an error when messageType does not match message type."""
    with pytest.raises(ValueError, match="Message type mismatch"):
        LiquoriceEnvelope(
            message=RFQQuoteMessage(rfqId=UUID("2aca5f16-defd-4f0c-9d4e-f219d69cbd7b"), levels=[]),
            messageType=MessageType.RFQ,
        )

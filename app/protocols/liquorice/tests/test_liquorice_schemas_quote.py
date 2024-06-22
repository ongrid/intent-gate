import json
from pathlib import Path
from uuid import UUID

import pytest
from hexbytes import HexBytes

from app.protocols.liquorice.schemas import (
    QuoteLevelLite,
    RFQQuoteMessage,
)

valid_quote_lite_envelope_text = (
    Path(__file__).parent / "data" / "liquorice_quote_lite.json"
).read_text()
valid_quote_lite_envelope_json = json.loads(valid_quote_lite_envelope_text)
valid_quote_level_dict = valid_quote_lite_envelope_json["message"]["levels"][0]


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


def test_level_signature_validation():
    """Test that level signatures can be in different formats."""
    level = valid_quote_level_dict.copy()
    del level["signature"]
    with pytest.raises(ValueError, match="Non-hexadecimal digit found"):
        QuoteLevelLite(**level, signature="0xbla")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="signature must be bytes or hex string"):
        QuoteLevelLite(**level, signature=123)  # type: ignore[arg-type]

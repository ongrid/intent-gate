import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID

import pytest

from app.protocols.liquorice.schemas import (
    IntentMetadata,
    LiquoriceEnvelope,
)

valid_rfq_envelope_text = (Path(__file__).parent / "data" / "liquorice_rfq.json").read_text()
valid_rfq_envelope_dict = json.loads(valid_rfq_envelope_text)
MAX_UINT256_STR = "115792089237316195423570985008687907853269984665640564039457584007913129639935"
MAX_UINT256_INT = 2**256 - 1

valid_quote_envelope_text = (
    Path(__file__).parent / "data" / "liquorice_quote_lite.json"
).read_text()


def test_parse_valid_rfq():
    """Test RFQMessage validation."""
    rfq = LiquoriceEnvelope.model_validate_json(json.dumps(valid_rfq_envelope_dict))
    assert rfq.messageType == "rfq"
    assert rfq.message.chainId == 42161
    assert rfq.message.solver == "portus"
    assert rfq.message.solverRfqId == UUID("95a0f428-a6c4-4207-81b2-e47436741e9b")
    assert rfq.message.rfqId == UUID("846063db-1769-438b-8002-00fd981603df")
    assert (
        rfq.message.nonce.hex()
        == "ade8af8413607c37361fcebe3b00cc3de354986c188efe9d6db0fa8c74843ad0"
    )
    assert rfq.message.baseToken == "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    assert rfq.message.quoteToken == "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    assert rfq.message.trader == "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
    assert rfq.message.effectiveTrader == "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
    assert rfq.message.baseTokenAmount == 6358600000
    assert rfq.message.quoteTokenAmount is None
    assert rfq.message.intentMetadata is not None
    assert isinstance(rfq.message.intentMetadata, IntentMetadata)
    assert rfq.message.intentMetadata.source == "cow_protocol"
    assert rfq.message.intentMetadata.content.auctionId == 3824359
    assert rfq.message.expiry == 1750707521  # seconds since epoch


def test_parse_valid_rfq_opposite_direction():
    rfq_opposite_dir = deepcopy(valid_rfq_envelope_dict)
    rfq_opposite_dir["message"]["baseTokenAmount"] = None
    rfq_opposite_dir["message"]["quoteTokenAmount"] = "6358600000"
    LiquoriceEnvelope.model_validate_json(json.dumps(rfq_opposite_dir))


def test_parse_valid_rfq_max_uint256():
    rfq_max_uint256 = deepcopy(valid_rfq_envelope_dict)
    rfq_max_uint256["message"]["baseTokenAmount"] = MAX_UINT256_STR
    rfq = LiquoriceEnvelope.model_validate_json(json.dumps(rfq_max_uint256))
    assert rfq.message.baseTokenAmount == MAX_UINT256_INT


def test_parse_rfq_when_bad_checksum_addresses():
    rfq_bad_address_csum = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_address_csum["message"][
        "baseToken"
    ] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"  # bad checksum address. All-lowercase
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_address_csum["message"][
        "baseToken"
    ] = "af88d065e77c8cc2239327c5edb3a432268e58"  # short
    with pytest.raises(ValueError, match="Bad Ethereum address"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_address_csum["message"]["quoteToken"] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_address_csum["message"]["trader"] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_address_csum["message"][
        "effectiveTrader"
    ] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))


def test_parse_rfq_when_bad_nonce():
    rfq_bad_nonce = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_nonce["message"][
        "nonce"
    ] = "ade8af8413607c37361fcebe3b00cc3de354986c188efe9d6db0fa8c74843ad"  # short nonce
    with pytest.raises(ValueError, match="nonce must be a 32-byte hex string"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_nonce))
    rfq_bad_nonce = deepcopy(valid_rfq_envelope_dict)
    rfq_bad_nonce["message"]["nonce"] = "bla"  # non-hex nonce
    with pytest.raises(ValueError, match="nonce must be a 32-byte hex string"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_nonce))


def test_parse_rfq_when_both_amounts_set():
    rfq_both_amounts = deepcopy(valid_rfq_envelope_dict)
    rfq_both_amounts["message"]["baseTokenAmount"] = "123456"
    rfq_both_amounts["message"]["quoteTokenAmount"] = "654321"
    with pytest.raises(
        ValueError, match="Exactly one of baseTokenAmount or quoteTokenAmount must be set"
    ):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_both_amounts))


def test_parse_rfq_when_both_amounts_missing():
    rfq_both_amounts_missing = deepcopy(valid_rfq_envelope_dict)
    rfq_both_amounts_missing["message"]["baseTokenAmount"] = None
    rfq_both_amounts_missing["message"]["quoteTokenAmount"] = None
    with pytest.raises(
        ValueError, match="Exactly one of baseTokenAmount or quoteTokenAmount must be set"
    ):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_both_amounts_missing))


def test_parse_rfq_raise_when_expiry_wrong():
    rfq_wrong_expiry = deepcopy(valid_rfq_envelope_dict)
    rfq_wrong_expiry["message"]["expiry"] = 2000000000_000  # milliseconds instead of seconds
    with pytest.raises(ValueError, match="Expiry must be a unix timestamp in seconds"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_wrong_expiry))
    rfq_wrong_expiry = deepcopy(valid_rfq_envelope_dict)
    rfq_wrong_expiry["message"]["expiry"] = "2000000000"  # string instead of int
    with pytest.raises(ValueError, match="Expiry must be a positive integer"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_wrong_expiry))

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

import pytest
from hexbytes import HexBytes
from web3 import Web3

from app.protocols.liquorice.schemas import (
    IntentMetadata,
    IntentMetadataContent,
    LiquoriceEnvelope,
    RFQMessage,
)

VALID_RFQ_EXAMPLE_DICT: Dict[str, Any] = {
    "messageType": "rfq",
    "message": {
        "chainId": 42161,
        "solver": "portus",
        "solverRfqId": "95a0f428-a6c4-4207-81b2-e47436741e9b",
        "rfqId": "846063db-1769-438b-8002-00fd981603df",
        "nonce": "ade8af8413607c37361fcebe3b00cc3de354986c188efe9d6db0fa8c74843ad0",
        "expiry": 1750707521,
        "baseToken": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "quoteToken": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "trader": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
        "effectiveTrader": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
        "baseTokenAmount": "6358600000",
        "quoteTokenAmount": None,
        "intentMetadata": {"source": "cow_protocol", "content": {"auctionId": 3824359}},
    },
    "timestamp": 1750707221629,
}
MAX_UINT256_STR = "115792089237316195423570985008687907853269984665640564039457584007913129639935"
MAX_UINT256_INT = 2**256 - 1

valid_quote_envelope_text = (
    Path(__file__).parent / "data" / "liquorice_quote_lite.json"
).read_text()


def test_parse_valid_rfq():
    """Test RFQMessage validation."""
    rfq = LiquoriceEnvelope.model_validate_json(json.dumps(VALID_RFQ_EXAMPLE_DICT))
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
    rfq_opposite_dir = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_opposite_dir["message"]["baseTokenAmount"] = None
    rfq_opposite_dir["message"]["quoteTokenAmount"] = "6358600000"
    LiquoriceEnvelope.model_validate_json(json.dumps(rfq_opposite_dir))


def test_parse_valid_rfq_max_uint256():
    rfq_max_uint256 = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_max_uint256["message"]["baseTokenAmount"] = MAX_UINT256_STR
    rfq = LiquoriceEnvelope.model_validate_json(json.dumps(rfq_max_uint256))
    assert rfq.message.baseTokenAmount == MAX_UINT256_INT


def test_parse_rfq_when_bad_checksum_addresses():
    rfq_bad_address_csum = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_address_csum["message"][
        "baseToken"
    ] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"  # bad checksum address. All-lowercase
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_address_csum["message"][
        "baseToken"
    ] = "af88d065e77c8cc2239327c5edb3a432268e58"  # short
    with pytest.raises(ValueError, match="Bad Ethereum address"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_address_csum["message"]["quoteToken"] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_address_csum["message"]["trader"] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))
    rfq_bad_address_csum = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_address_csum["message"][
        "effectiveTrader"
    ] = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
    with pytest.raises(ValueError, match="Bad Ethereum checksum"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_address_csum))


def test_parse_rfq_when_bad_nonce():
    rfq_bad_nonce = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_nonce["message"][
        "nonce"
    ] = "ade8af8413607c37361fcebe3b00cc3de354986c188efe9d6db0fa8c74843ad"  # short nonce
    with pytest.raises(ValueError, match="nonce must be a 32-byte hex string"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_nonce))
    rfq_bad_nonce = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_bad_nonce["message"]["nonce"] = "bla"  # non-hex nonce
    with pytest.raises(ValueError, match="nonce must be a 32-byte hex string"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_bad_nonce))


def test_parse_rfq_when_both_amounts_set():
    rfq_both_amounts = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_both_amounts["message"]["baseTokenAmount"] = "123456"
    rfq_both_amounts["message"]["quoteTokenAmount"] = "654321"
    with pytest.raises(
        ValueError, match="Exactly one of baseTokenAmount or quoteTokenAmount must be set"
    ):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_both_amounts))


def test_parse_rfq_when_both_amounts_missing():
    rfq_both_amounts_missing = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_both_amounts_missing["message"]["baseTokenAmount"] = None
    rfq_both_amounts_missing["message"]["quoteTokenAmount"] = None
    with pytest.raises(
        ValueError, match="Exactly one of baseTokenAmount or quoteTokenAmount must be set"
    ):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_both_amounts_missing))


def test_parse_rfq_raise_when_expiry_wrong():
    rfq_wrong_expiry = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_wrong_expiry["message"]["expiry"] = 2000000000_000  # milliseconds instead of seconds
    with pytest.raises(ValueError, match="Expiry must be a unix timestamp in seconds"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_wrong_expiry))
    rfq_wrong_expiry = deepcopy(VALID_RFQ_EXAMPLE_DICT)
    rfq_wrong_expiry["message"]["expiry"] = "2000000000"  # string instead of int
    with pytest.raises(ValueError, match="Expiry must be a positive integer"):
        LiquoriceEnvelope.model_validate_json(json.dumps(rfq_wrong_expiry))


def test_envelope_init_dto_infer_rfq_type():
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

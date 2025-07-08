import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from eth_typing import HexStr
from hexbytes import HexBytes
from web3.main import to_checksum_address

from app.protocols.liquorice.const import LIQUORICE_SETTLEMENT_ADDRESS
from app.protocols.liquorice.schemas import RFQMessage, RFQQuoteMessage
from app.protocols.liquorice.signer import SignableRfqQuoteLevel, Web3Signer

# Signable object vector example is taken from
# https://liquorice.gitbook.io/liquorice-docs/for-market-makers/basic-market-making-api
signable_lvl_dict = json.loads((Path(__file__).parent / "data" / "signable_lvl.json").read_text())
signable_lvl_dict["nonce"] = HexBytes(signable_lvl_dict["nonce"])
signable_lvl = SignableRfqQuoteLevel(**signable_lvl_dict)
del signable_lvl_dict["recipient"]
rfq_dict = json.loads((Path(__file__).parent / "data" / "liquorice_rfq.json").read_text())
quote_dict = json.loads((Path(__file__).parent / "data" / "liquorice_quote_lite.json").read_text())
rfq_msg = RFQMessage(**rfq_dict["message"])
quote_msg = RFQQuoteMessage(**quote_dict["message"])


# This is a private key derived from from well-known test mnemonic at index #0:
# "test test test test test test test test test test test junk"
# Account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
# NEVER EVER use this private key in production!
PRIV_KEY = HexStr("ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
ACCOUNT_ADDRESS = to_checksum_address("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")


@pytest.fixture
def signer():
    chain_registry = Mock()
    chain_registry.chain_by_id = {
        42161: Mock(
            liquorice_settlement_address=LIQUORICE_SETTLEMENT_ADDRESS,
            active=True,
            skeeper_address=ACCOUNT_ADDRESS,
        ),
    }
    return Web3Signer(chain_registry, PRIV_KEY)


def test_order_digest():
    assert signable_lvl.hash == HexBytes(
        "0x2342c2e81befd9dda11c9e769d6d867e347d5b84a0137bf9fa31acbe7ee4f5ac"
    )


def test_liquorice_signer(signer):
    """Test the Liquorice signer with a signable level."""
    signed_quote = signer.sign_quote_levels(rfq_msg, quote_msg)
    # Check if the recipient and signer addresses are set correctly
    assert signed_quote.levels[0].recipient == signer.account.address
    assert signed_quote.levels[0].signer == signer.account.address
    # Check if the signature is present
    assert isinstance(signed_quote.levels[0].signature, HexBytes)
    assert signed_quote.levels[0].signature == HexBytes(
        "0x6d512bc0bf3388a27968202e7b516e4777fda5b06be7b8bcd04ad37c103d776b3ea2132045a41e07e7aa9f552c6ad9fda33d53904d09a7cc11abd4a73f024b401c"
    )

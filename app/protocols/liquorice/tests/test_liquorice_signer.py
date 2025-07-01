import json
from pathlib import Path

from hexbytes import HexBytes

from app.protocols.liquorice.signer import SignableRfqQuoteLevel

# Signable object vector example is taken from
# https://liquorice.gitbook.io/liquorice-docs/for-market-makers/basic-market-making-api
signable_lvl_dict = json.loads((Path(__file__).parent / "data" / "signable_lvl.json", "r").read_text())
signable_lvl = SignableRfqQuoteLevel(**signable_lvl_dict)


def test_order_digest():
    assert signable_lvl.hash == HexBytes(
        "0x2342c2e81befd9dda11c9e769d6d867e347d5b84a0137bf9fa31acbe7ee4f5ac"
    )

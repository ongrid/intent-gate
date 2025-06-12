import pytest
from eth_typing import ChecksumAddress, HexStr

from app.evm.helpers import encode_address


@pytest.mark.parametrize(
    "input_address,expected_output",
    [
        (
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            HexStr("0x000000000000000000000000742d35cc6634c0532925a3b844bc454e4438f44e"),
        ),
        (
            "0x0000000000000000000000000000000000000000",
            HexStr("0x0000000000000000000000000000000000000000000000000000000000000000"),
        ),
        (
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            HexStr("0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"),
        ),
    ],
)
def test_pad_address(input_address: ChecksumAddress, expected_output: HexStr) -> None:
    """Test address padding to 32 bytes."""
    assert encode_address(input_address) == expected_output


def test_pad_address_invalid_input() -> None:
    """Test padding with invalid address format raises ValueError."""
    with pytest.raises(ValueError):
        encode_address("invalid")

    with pytest.raises(ValueError):
        encode_address("0xinvalid")

    with pytest.raises(ValueError):
        encode_address("0x123")

    with pytest.raises(ValueError):
        encode_address("0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2")  # Broken checksum

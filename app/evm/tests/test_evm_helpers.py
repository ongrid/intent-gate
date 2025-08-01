from uuid import UUID

import pytest
from eth_typing import ChecksumAddress, HexStr
from hexbytes import HexBytes

from app.evm.helpers import encode_address, uuid_to_topic


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


def test_uuid_to_topic():
    """Rust test vector from Liquorice team
    let rfq_id = Uuid::from_str("c61c7b1d-86fa-402e-ba12-fb49c9c55cf8").unwrap();
    let event_rfq_id = keccak256(rfq_id.to_string().as_bytes());
    println!("{}", event_rfq_id); // 0x5205ecfc2e68786dcf34fffa27fb32e55f3c1c740959eb95c8b37ad61504a5c8
    """
    rfq_id = UUID("c61c7b1d-86fa-402e-ba12-fb49c9c55cf8")
    event_rfq_id = uuid_to_topic(rfq_id)
    assert event_rfq_id == HexBytes(
        "0x5205ecfc2e68786dcf34fffa27fb32e55f3c1c740959eb95c8b37ad61504a5c8"
    )

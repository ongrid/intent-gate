# pylint: disable=redefined-outer-name
"""Tests for ERC20Token decimal conversion methods."""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from web3.main import to_checksum_address

from app.schemas.token import ERC20Token


@pytest.fixture
def mock_chain():
    """Mock chain for testing."""
    chain = Mock()
    chain.id = 1
    chain.name = "Ethereum"
    return chain


@pytest.fixture
def eth_token(mock_chain):
    """Standard 18-decimal token (like ETH, most ERC20s)."""
    return ERC20Token(
        name="Ethereum",
        symbol="ETH",
        chain=mock_chain,
        address=to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
        decimals=18,
    )


@pytest.fixture
def usdc_token(mock_chain):
    """6-decimal token (like USDC)."""
    return ERC20Token(
        name="USD Coin",
        symbol="USDC",
        chain=mock_chain,
        address=to_checksum_address("0xA0b86a33E6441E72bF7f0a29c0DFD33F5b4f7F45"),
        decimals=6,
    )


@pytest.fixture
def wbtc_token(mock_chain):
    """8-decimal token (like WBTC)."""
    return ERC20Token(
        name="Wrapped Bitcoin",
        symbol="WBTC",
        chain=mock_chain,
        address=to_checksum_address("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
        decimals=8,
    )


class TestRawToDecimal:
    """Test raw_to_decimal method."""

    def test_standard_18_decimals(self, eth_token):
        """Test conversion with standard 18 decimals."""
        # 1 ETH = 1 * 10^18 wei
        assert eth_token.raw_to_decimal(1000000000000000000) == Decimal("1.0")

        # 1.5 ETH
        assert eth_token.raw_to_decimal(1500000000000000000) == Decimal("1.5")

        # 0.1 ETH
        assert eth_token.raw_to_decimal(100000000000000000) == Decimal("0.1")

        # Very small amount (1 wei)
        assert eth_token.raw_to_decimal(1) == Decimal("0.000000000000000001")

    def test_6_decimals_usdc(self, usdc_token):
        """Test conversion with 6 decimals (USDC)."""
        # 1 USDC = 1 * 10^6
        assert usdc_token.raw_to_decimal(1000000) == Decimal("1.0")

        # 100.50 USDC
        assert usdc_token.raw_to_decimal(100500000) == Decimal("100.5")

        # 0.01 USDC (1 cent)
        assert usdc_token.raw_to_decimal(10000) == Decimal("0.01")

        # Smallest unit
        assert usdc_token.raw_to_decimal(1) == Decimal("0.000001")

    def test_8_decimals_wbtc(self, wbtc_token):
        """Test conversion with 8 decimals (WBTC)."""
        # 1 WBTC = 1 * 10^8 satoshi
        assert wbtc_token.raw_to_decimal(100000000) == Decimal("1.0")

        # 0.5 WBTC
        assert wbtc_token.raw_to_decimal(50000000) == Decimal("0.5")

        # 1 satoshi
        assert wbtc_token.raw_to_decimal(1) == Decimal("0.00000001")

    def test_zero_amount(self, eth_token):
        """Test zero amount conversion."""
        assert eth_token.raw_to_decimal(0) == Decimal("0")

    def test_large_amounts(self, eth_token):
        """Test very large amounts."""
        # 1 million ETH
        million_eth = 1000000 * 10**18
        assert eth_token.raw_to_decimal(million_eth) == Decimal("1000000")

        # Total supply-like amount
        total_supply = 21000000 * 10**18
        assert eth_token.raw_to_decimal(total_supply) == Decimal("21000000")

    def test_precision_maintained(self, eth_token):
        """Test that precision is maintained for complex decimal values."""
        # 1.123456789012345678 ETH (max precision for 18 decimals)
        raw_amount = 1123456789012345678
        expected = Decimal("1.123456789012345678")
        assert eth_token.raw_to_decimal(raw_amount) == expected


class TestDecimalToRaw:
    """Test decimal_to_raw method."""

    def test_string_input_18_decimals(self, eth_token):
        """Test string input with 18 decimals."""
        assert eth_token.decimal_to_raw("1.0") == 1000000000000000000
        assert eth_token.decimal_to_raw("1.5") == 1500000000000000000
        assert eth_token.decimal_to_raw("0.1") == 100000000000000000
        assert eth_token.decimal_to_raw("0.000000000000000001") == 1

    def test_int_input(self, eth_token):
        """Test integer input."""
        assert eth_token.decimal_to_raw(1) == 1000000000000000000
        assert eth_token.decimal_to_raw(5) == 5000000000000000000
        assert eth_token.decimal_to_raw(0) == 0

    def test_float_input(self, eth_token):
        """Test float input."""
        assert eth_token.decimal_to_raw(1.0) == 1000000000000000000
        assert eth_token.decimal_to_raw(1.5) == 1500000000000000000
        assert eth_token.decimal_to_raw(0.1) == 100000000000000000

    def test_decimal_input(self, eth_token):
        """Test Decimal input."""
        assert eth_token.decimal_to_raw(Decimal("1.0")) == 1000000000000000000
        assert eth_token.decimal_to_raw(Decimal("1.5")) == 1500000000000000000
        assert eth_token.decimal_to_raw(Decimal("0.000000000000000001")) == 1

    def test_6_decimals_usdc(self, usdc_token):
        """Test conversion with 6 decimals."""
        assert usdc_token.decimal_to_raw("1.0") == 1000000
        assert usdc_token.decimal_to_raw("100.50") == 100500000
        assert usdc_token.decimal_to_raw("0.01") == 10000
        assert usdc_token.decimal_to_raw("0.000001") == 1

    def test_8_decimals_wbtc(self, wbtc_token):
        """Test conversion with 8 decimals."""
        assert wbtc_token.decimal_to_raw("1.0") == 100000000
        assert wbtc_token.decimal_to_raw("0.5") == 50000000
        assert wbtc_token.decimal_to_raw("0.00000001") == 1

    def test_zero_amount(self, eth_token):
        """Test zero amount conversion."""
        assert eth_token.decimal_to_raw("0") == 0
        assert eth_token.decimal_to_raw(0) == 0
        assert eth_token.decimal_to_raw(0.0) == 0

    def test_large_amounts(self, eth_token):
        """Test very large amounts."""
        # 1 million ETH
        assert eth_token.decimal_to_raw("1000000") == 1000000 * 10**18

        # Total supply-like amount
        assert eth_token.decimal_to_raw("21000000") == 21000000 * 10**18

    def test_precision_edge_cases(self, eth_token):
        """Test precision edge cases."""
        # Maximum precision for 18 decimals
        max_precision = "1.123456789012345678"
        expected = 1123456789012345678
        assert eth_token.decimal_to_raw(max_precision) == expected

        # Scientific notation
        assert eth_token.decimal_to_raw("1e-18") == 1
        assert eth_token.decimal_to_raw("1e18") == 1000000000000000000000000000000000000

    def test_rounding_behavior(self, eth_token):
        """Test rounding behavior for amounts with too much precision."""
        # More precision than 18 decimals - should truncate
        result = eth_token.decimal_to_raw("1.0000000000000000001")
        expected = 1000000000000000000  # Truncated to 18 decimals
        assert result == expected

    def test_negative_amounts_not_supported(self, eth_token):
        """Test that negative amounts are handled (should not crash)."""
        # Note: This depends on your business logic requirements
        # For now, just test that it doesn't crash
        result = eth_token.decimal_to_raw("-1.0")
        assert result == -1000000000000000000  # Negative raw amount


class TestBalanceProperty:
    """Test balance property."""

    def test_balance_property_18_decimals(self, eth_token):
        """Test balance property with 18 decimals."""
        eth_token.raw_balance = 1500000000000000000  # 1.5 ETH
        assert eth_token.balance == Decimal("1.5")

    def test_balance_property_6_decimals(self, usdc_token):
        """Test balance property with 6 decimals."""
        usdc_token.raw_balance = 100500000  # 100.5 USDC
        assert usdc_token.balance == Decimal("100.5")

    def test_balance_property_8_decimals(self, wbtc_token):
        """Test balance property with 8 decimals."""
        wbtc_token.raw_balance = 50000000  # 0.5 WBTC
        assert wbtc_token.balance == Decimal("0.5")

    def test_zero_balance(self, eth_token):
        """Test zero balance."""
        eth_token.raw_balance = 0
        assert eth_token.balance == Decimal("0")

    def test_balance_updates_dynamically(self, eth_token):
        """Test that balance property updates when raw_balance changes."""
        # Initial balance
        eth_token.raw_balance = 1000000000000000000  # 1 ETH
        assert eth_token.balance == Decimal("1.0")

        # Update balance
        eth_token.raw_balance = 2000000000000000000  # 2 ETH
        assert eth_token.balance == Decimal("2.0")

    def test_balance_precision(self, eth_token):
        """Test balance precision with complex values."""
        eth_token.raw_balance = 1123456789012345678  # Max precision
        assert eth_token.balance == Decimal("1.123456789012345678")


class TestRoundTripConversion:
    """Test round-trip conversion (raw -> decimal -> raw)."""

    def test_round_trip_18_decimals(self, eth_token):
        """Test round-trip conversion maintains precision."""
        original_raw = 1500000000000000000  # 1.5 ETH

        # Convert to decimal and back
        decimal_amount = eth_token.raw_to_decimal(original_raw)
        converted_raw = eth_token.decimal_to_raw(decimal_amount)

        assert converted_raw == original_raw

    def test_round_trip_6_decimals(self, usdc_token):
        """Test round-trip conversion with 6 decimals."""
        original_raw = 100500000  # 100.5 USDC

        decimal_amount = usdc_token.raw_to_decimal(original_raw)
        converted_raw = usdc_token.decimal_to_raw(decimal_amount)

        assert converted_raw == original_raw

    def test_round_trip_8_decimals(self, wbtc_token):
        """Test round-trip conversion with 8 decimals."""
        original_raw = 50000000  # 0.5 WBTC

        decimal_amount = wbtc_token.raw_to_decimal(original_raw)
        converted_raw = wbtc_token.decimal_to_raw(decimal_amount)

        assert converted_raw == original_raw

    def test_round_trip_edge_cases(self, eth_token):
        """Test round-trip with edge cases."""
        test_cases = [
            0,  # Zero
            1,  # Minimum unit
            1000000000000000000,  # 1 ETH
            1123456789012345678,  # Max precision
            21000000000000000000000000,  # Large amount
        ]

        for original_raw in test_cases:
            decimal_amount = eth_token.raw_to_decimal(original_raw)
            converted_raw = eth_token.decimal_to_raw(decimal_amount)
            assert converted_raw == original_raw, f"Failed for {original_raw}"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_decimal_input(self, eth_token):
        """Test handling of invalid decimal inputs."""
        with pytest.raises(Exception):  # Should raise some form of exception
            eth_token.decimal_to_raw("invalid_number")

    def test_empty_string_input(self, eth_token):
        """Test handling of empty string input."""
        with pytest.raises(Exception):
            eth_token.decimal_to_raw("")

    def test_none_input(self, eth_token):
        """Test handling of None input."""
        with pytest.raises(Exception):
            eth_token.decimal_to_raw(None)

    def test_very_large_numbers(self, eth_token):
        """Test handling of very large numbers."""
        # Should not crash, but might overflow
        large_number = "999999999999999999999999999999"
        result = eth_token.decimal_to_raw(large_number)
        assert isinstance(result, int)

    def test_negative_raw_amount(self, eth_token):
        """Test handling of negative raw amounts."""
        # Should work mathematically
        result = eth_token.raw_to_decimal(-1000000000000000000)
        assert result == Decimal("-1.0")

from ..chain import Chain
from ..token import ERC20Token


def test_token_hashable():
    """Test that ERC20Token can be used in sets and as dict/graph keys for networkx compatibility"""
    chain = Chain(
        name="Arbitrum",
        id=42161,
        liquorice_settlement_address="0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167",
    )

    # Same token with different metadata - WILL collide to the same hash
    token1 = ERC20Token(
        name="USD Coin",
        symbol="USDC",
        chain=chain,
        address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    )
    token2 = ERC20Token(
        name="USDC",
        symbol="USDC.e",
        chain=chain,
        address="0xaf88d065e77c8cc2239327c5edb3a432268e5831",  # lowercase
    )

    # Different token
    token3 = ERC20Token(
        name="USD Tether",
        symbol="USDT",
        chain=chain,
        address="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    )

    # Test set behavior
    tokens = {token1, token2, token3}
    assert len(tokens) == 2  # token1 and token2 are equal

    # Test dict/graph key behavior
    token_dict = {token1: "value1"}
    assert token_dict[token2] == "value1"  # Can look up with equivalent token
    assert token1 in token_dict
    assert token2 in token_dict
    assert token3 not in token_dict

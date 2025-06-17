# pylint: disable=missing-module-docstring,duplicate-code

from ...schemas.chain import Chain
from ...schemas.token import ERC20Token

CHAIN_ID = 1
CHAIN = Chain(
    id=CHAIN_ID,
    name="Ethereum",
    short_names=["eth", "ethereum"],
    gas_token="ETH",
    poa=False,
    active=False,
    liquorice_settlement_address="0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167",
)
USDT = ERC20Token(
    name="Tether USDT",
    symbol="USDT",
    chain=CHAIN,
    address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    decimals=6,
)
BNB = ERC20Token(
    name="BNB",
    symbol="BNB",
    chain=CHAIN,
    address="0xB8c77482e45F1F44dE1745F52C74426C631bDD52",
    decimals=18,
)
USDC = ERC20Token(
    name="Circle USDC",
    symbol="USDC",
    chain=CHAIN,
    address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    decimals=6,
)
WETH = ERC20Token(
    name="Wrapped Ether",
    symbol="WETH",
    chain=CHAIN,
    address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    decimals=18,
)
WBTC = ERC20Token(
    name="Wrapped BTC",
    symbol="WBTC",
    chain=CHAIN,
    address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    decimals=8,
)
DAI = ERC20Token(
    name="Maker DAI",
    symbol="DAI",
    chain=CHAIN,
    address="0x6B175474E89094C44Da98b954EedeAC495271d0F",
    decimals=18,
)
COW_ETH = ERC20Token(
    name="CoW psewdo ETH",
    symbol="cowETH",
    chain=CHAIN,
    address="0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    decimals=18,
)

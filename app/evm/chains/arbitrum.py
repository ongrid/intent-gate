# pylint: disable=missing-module-docstring,duplicate-code
from web3.main import to_checksum_address

from ...schemas.chain import Chain
from ...schemas.token import ERC20Token

CHAIN_ID = 42161
CHAIN = Chain(
    id=CHAIN_ID,
    name="Arbitrum One",
    short_names=["arb", "arbitrum"],
    gas_token="ETH",
    poa=False,
    liquorice_settlement_address=to_checksum_address("0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167"),
)
USDT = ERC20Token(
    name="Arbitrum USDT",
    symbol="USDT",
    chain=CHAIN,
    address=to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"),
    decimals=6,
)
USDC_BR = ERC20Token(
    name="Arbitrum USDC Bridged",
    symbol="USDC",
    chain=CHAIN,
    address=to_checksum_address("0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"),
    decimals=6,
)
USDC = ERC20Token(
    name="Arbitrum USDC",
    symbol="USDC",
    chain=CHAIN,
    address=to_checksum_address("0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
    decimals=6,
)
WBTC = ERC20Token(
    name="Arbitrum WBTC",
    symbol="WBTC",
    chain=CHAIN,
    address=to_checksum_address("0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"),
    decimals=8,
)
WETH = ERC20Token(
    name="Arbitrum WETH",
    symbol="WETH",
    chain=CHAIN,
    address=to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"),
    decimals=18,
)
UNI = ERC20Token(
    name="Arbitrum UNI",
    symbol="UNI",
    chain=CHAIN,
    address=to_checksum_address("0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0"),
    decimals=18,
)
ARB = ERC20Token(
    name="Arbitrum ARB",
    symbol="ARB",
    chain=CHAIN,
    address=to_checksum_address("0x912CE59144191C1204E64559FE8253a0e49E6548"),
    decimals=18,
)
DAI = ERC20Token(
    name="Arbitrum DAI",
    symbol="DAI",
    chain=CHAIN,
    address=to_checksum_address("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"),
    decimals=18,
)
USDS = ERC20Token(
    name="Arbitrum USDS",
    symbol="USDS",
    chain=CHAIN,
    address=to_checksum_address("0x6491c05A82219b8D1479057361ff1654749b876b"),
    decimals=18,
)
WST_ETH = ERC20Token(
    name="Arbitrum wstETH",
    symbol="wstETH",
    chain=CHAIN,
    address=to_checksum_address("0x5979D7b546E38E414F7E9822514be443A4800529"),
    decimals=18,
)
COW = ERC20Token(
    name="CoW",
    symbol="COW",
    chain=CHAIN,
    address=to_checksum_address("0xcb8b5CD20BdCaea9a010aC1F8d835824F5C87A04"),
    decimals=18,
)
CB_BTC = ERC20Token(
    name="Coinbase Wrapped BTC",
    symbol="cbBTC",
    chain=CHAIN,
    address=to_checksum_address("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"),
    decimals=8,
)
COW_ETH = ERC20Token(
    name="CoW psewdo ETH",
    symbol="cowETH",
    chain=CHAIN,
    address=to_checksum_address("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"),
    decimals=18,
)

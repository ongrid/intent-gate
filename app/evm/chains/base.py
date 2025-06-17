# pylint: disable=missing-module-docstring,duplicate-code

from ...schemas.chain import Chain
from ...schemas.token import ERC20Token

CHAIN_ID = 8453
CHAIN = Chain(
    id=CHAIN_ID,
    name="Base",
    short_names=["base"],
    gas_token="BASE",
    poa=False,
    active=False,
    liquorice_settlement_address="0xAcA684A3F64e0eae4812B734E3f8f205D3EEd167",
)
WETH = ERC20Token(
    name="Base WETH",
    symbol="WETH",
    chain=CHAIN,
    address="0x4200000000000000000000000000000000000006",
    decimals=18,
)
CB_BTC = ERC20Token(
    name="Coinbase Wrapped BTC",
    symbol="cbBTC",
    chain=CHAIN,
    address="0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
    decimals=8,
)
USDC = ERC20Token(
    name="USDC on Base",
    symbol="USDC",
    chain=CHAIN,
    address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    decimals=6,
)
WBTC = ERC20Token(
    name="Wrapped BTC",
    symbol="WBTC",
    chain=CHAIN,
    address="0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",
    decimals=8,
)

"""Chain schema(s) definition."""

# pylint: disable=R0902

from dataclasses import dataclass, field
from typing import List, Optional

from eth_typing import ChecksumAddress


@dataclass
class Chain:
    """Represents a blockchain network with its properties and configuration."""

    id: int
    liquorice_settlement_address: ChecksumAddress
    name: str = "unknown"
    short_names: List[str] = field(default_factory=list)
    gas_token: str = "ETH"
    poa: bool = False
    active: bool = False
    tokens: List = field(default_factory=list)
    ws_rpc_url: Optional[str] = None
    skeeper_address: Optional[ChecksumAddress] = None

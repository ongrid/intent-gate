"""Chain registry for managing runtime chain configurations and tokens."""

import importlib
import logging
import os
import pkgutil
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from web3 import Web3

from ..schemas.chain import Chain
from ..schemas.token import ERC20Token

CHAINS_INVENTORY_MODULE = "app.evm.chains"
CHAIN_WS_URL_ENV_POSTFIX = "_WS_URL"

log = logging.getLogger(__name__)


class ChainRegistry:
    """Registry for managing multiple blockchain configurations."""

    chains: List[Chain]
    chain_by_id: Dict[Union[str, int], Chain]
    token_by_chain_id_and_address: Dict[Tuple[int, str], ERC20Token]

    def __init__(self) -> None:
        """Initialize an empty ChainRegistry."""
        self.chains = []
        self.chain_by_id = {}
        self.token_by_chain_id_and_address = {}

    @classmethod
    def from_chains_inventory(cls) -> "ChainRegistry":
        """Create a ChainRegistry with default chains."""

        registry = cls()

        inventory_pkg = importlib.import_module(CHAINS_INVENTORY_MODULE)

        log.debug("Loading chains from inventory module: %s", CHAINS_INVENTORY_MODULE)
        for chain_inv_module_info in pkgutil.iter_modules(inventory_pkg.__path__):
            chain_inv_module_name = chain_inv_module_info.name
            if chain_inv_module_name == "__init__":
                continue  # pragma: no cover

            log.debug("Loading chain %s from inventory module", chain_inv_module_name)
            chain_inv_module = importlib.import_module(
                f"{CHAINS_INVENTORY_MODULE}.{chain_inv_module_name}"
            )

            for attr_name in dir(chain_inv_module):
                attr = getattr(chain_inv_module, attr_name)

                if isinstance(attr, Chain):
                    registry.chains.append(attr)
                    registry.chain_by_id[attr.id] = attr
                    log.debug(
                        "Added Chain id: %s, name: %s, short_names: %s",
                        attr.id,
                        attr.name,
                        attr.short_names,
                    )
                if isinstance(attr, ERC20Token):
                    registry.token_by_chain_id_and_address[
                        (attr.chain.id, Web3.to_checksum_address(attr.address))
                    ] = attr
                    attr.chain.tokens.append(attr)
                    log.debug(
                        "Added Token address: %s, name: %s, chain: %s",
                        attr.address,
                        attr.name,
                        attr.chain.id,
                    )

        return registry

    @staticmethod
    def _is_valid_ws_url(url: str) -> bool:
        """Validate if URL is a valid WebSocket URL."""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme in ("ws", "wss"))
        except:  # pragma: no cover  # noqa: E722  # pylint: disable=bare-except
            return False

    def from_env(self) -> None:
        """Enrich a ChainRegistry with data from env variables, especially RPC nodes URLs."""
        assert (
            self.chains
        ), "ChainRegistry must be initialized with chains before calling from_env()"
        log.debug("Enriching ChainRegistry with environment variables")
        for chain in self.chains:
            for chain_short_name in chain.short_names:
                env_var = f"{chain_short_name.upper()}{CHAIN_WS_URL_ENV_POSTFIX}"
                ws_rpc_url = os.getenv(env_var)
                if ws_rpc_url:
                    if not self._is_valid_ws_url(ws_rpc_url):
                        raise ValueError(f"Invalid WebSocket URL in {env_var}: {ws_rpc_url}")
                    log.info(
                        "Setting RPC URL for chain %s(%s): %s",
                        chain.short_names[0],
                        chain.id,
                        ws_rpc_url,
                    )
                    chain.ws_rpc_url = ws_rpc_url
                    break
            else:
                raise ValueError(
                    f"Chain {chain.name} ({chain.id}) does not have a valid RPC URL set"
                )

    def get_chain_by_id(self, chain_id: int) -> Optional[Chain]:
        """Get a chain instance by its name or ID."""
        return self.chain_by_id.get(chain_id)

    def get_token_by_chain_id_and_address(
        self, chain_id: int, address: str
    ) -> Optional[ERC20Token]:
        """Get a token instance by chain id and address"""
        return self.token_by_chain_id_and_address.get(
            (chain_id, Web3.to_checksum_address(address))
        )

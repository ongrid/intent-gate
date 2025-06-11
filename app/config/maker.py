"""Configuration module for maker settings."""

import logging
import os
import uuid

from pydantic.dataclasses import dataclass
from web3 import Web3

log = logging.getLogger(__name__)


@dataclass
class MakerConfig:
    """Configuration for maker service authentication and endpoints.

    Handles authentication credentials, websocket connections, and blockchain addresses
    for the maker service. Configuration can be loaded from environment variables.

    Attributes:
        maker (str): Maker session ID for authentication
        authorization (str): UUID authorization token for maker session
        signer_priv_key (str): Hex Private key for signing quotes
        maker_ws_url (str): WebSocket URL for maker service connection
        settlement_address (str): Ethereum address of the settlement contract
    """

    maker: str
    authorization: str
    signer_priv_key: str
    maker_ws_url: str = "wss://api.liquorice.tech/v1/maker/ws"
    settlement_address: str = "0x5210Dc2Fd7094BF596Bf19E15d1510873D30d15c"  # Same for all chains

    @classmethod
    def from_env(cls) -> "MakerConfig":
        """Create MakerConfig from environment variables.
        Returns:
            MakerConfig: Instance with environment values

        Raises:
            ValueError: If MAKER_SESS_ID, MAKER_SESS_AUTH (UUID),
                        or SIGNER_PRIV_KEY are missing or invalid
        """
        maker = os.getenv("MAKER_SESS_ID")
        if not maker:
            raise ValueError("MAKER_SESS_ID env var is not set")
        log.debug("Using maker session ID: %s", maker)

        authorization = os.getenv("MAKER_SESS_AUTH")
        if not authorization:
            raise ValueError("MAKER_SESS_AUTH env var is not set")
        try:
            uuid.UUID(authorization)
        except Exception as e:
            raise ValueError(f"MAKER_SESS_AUTH must be a valid UUID, got: {e}") from e
        log.debug("Using sess authorization: %s", authorization)

        signer_priv_key = os.getenv("SIGNER_PRIV_KEY")
        if not signer_priv_key:
            raise ValueError("SIGNER_PRIV_KEY env var is not set")
        try:
            account = Web3().eth.account.from_key(signer_priv_key)
        except Exception as e:
            raise ValueError(f"Invalid SIGNER_PRIV_KEY: {e}") from e
        log.debug("Using account %s derived from SIGNER_PRIV_KEY", account.address)

        return cls(
            maker=maker,
            authorization=authorization,
            signer_priv_key=signer_priv_key,
        )

"""FastAPI application entry point for NMF WebSocket gateway.

This module initializes the FastAPI application and sets up WebSocket endpoints
for handling NMF protocol connections.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config.maker import MakerConfig
from app.evm.registry import ChainRegistry
from app.evm.service import ChainServiceMgr
from app.log.log import get_uvicorn_log_config, setup_logging
from app.markets.markets import MarketState
from app.metrics.health import CounterHealthChecker, HealthService
from app.metrics.metrics import metrics, metrics_router
from app.protocols.liquorice.client import LiquoriceClient
from app.protocols.liquorice.signer import Web3Signer
from app.quoter.quoter import LiquoriceQuoter

setup_logging()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context manager for initializing services."""
    log.info("Initializing chain registry...")
    chain_rg = ChainRegistry.from_chains_inventory()
    log.info("Chain registry initialized")
    log.info("Enriching chain registry with environment variables...")
    chain_rg.from_env()
    log.info("Initializing intent gateway configuration...")
    cfg_maker = MakerConfig.from_env()
    log.info("Maker configuration loaded: %s", cfg_maker)
    log.info("Initializing Liquorice Signer...")
    liquorice_signer = Web3Signer(chain_rg, cfg_maker.signer_priv_key)
    log.info("Liquorice Signer initialized with account: %s", liquorice_signer.account.address)
    markets = MarketState()
    cs_mgr = ChainServiceMgr(chain_rg, markets)
    log.info("Starting intent gateway...")
    chain_svc_mgr_task = asyncio.create_task(cs_mgr.run())  # long-lived coroutine
    log.info("Starting Liquorice client...")
    liq_client = LiquoriceClient(cfg_maker)
    liquorice_client_task = asyncio.create_task(
        liq_client.run()
    )  # long-lived coroutine for Liquorice client
    log.info("Starting Quoter service...")
    quoter = LiquoriceQuoter(liq_client.out_rfqs, liq_client.in_quotes, markets, liquorice_signer)
    quoter_task = asyncio.create_task(quoter.run())  # long-lived coroutine for Quoter
    log.info("Intent gateway started successfully")
    try:
        yield
    finally:
        logging.info("Shutting down ChainServiceManager...")
        await cs_mgr.shutdown()  # graceful stop
        chain_svc_mgr_task.cancel()
        liquorice_client_task.cancel()
        quoter_task.cancel()
        try:
            await chain_svc_mgr_task
            await liquorice_client_task
            await quoter_task
        except asyncio.CancelledError:
            pass


health_svc = HealthService()
health_svc.add_checker(
    CounterHealthChecker(
        metrics.rfqs_total, interval=60, label_key="status", label_values=["QUOTE_SENT"]
    ),
    name="rfq",
)

app = FastAPI(
    title="Intent Gateway",
    description="WebSocket gateway for Liquorice protocol",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_svc.router)
app.include_router(metrics_router)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_config=get_uvicorn_log_config(),
    )

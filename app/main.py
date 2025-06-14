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
    cs_mgr = ChainServiceMgr(chain_rg)
    log.info("Starting intent gateway...")
    task = asyncio.create_task(cs_mgr.run())  # long-lived coroutine
    try:
        yield
    finally:
        logging.info("Shutting down ChainServiceManager...")
        await cs_mgr.shutdown()  # graceful stop
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Intent Gateway",
    description="WebSocket gateway for Liquorice protocol",
    version="0.1.0",
    lifespan=lifespan,
)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_config=get_uvicorn_log_config(),
    )

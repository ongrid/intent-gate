"""FastAPI application entry point for NMF WebSocket gateway.

This module initializes the FastAPI application and sets up WebSocket endpoints
for handling NMF protocol connections.
"""

import logging

import uvicorn
from fastapi import FastAPI

from app.log.log import get_uvicorn_log_config, setup_logging

setup_logging()
log = logging.getLogger(__name__)
log.info("Starting intent gateway...")


app = FastAPI(
    title="Intent Gateway", description="WebSocket gateway for Liquorice protocol", version="0.1.0"
)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_config=get_uvicorn_log_config(),
    )

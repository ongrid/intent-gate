"""Tests for health endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.health.router import health_router
from app.health.schemas import HealthResponse, HealthStatus


@pytest.fixture
def client():
    """Create test client."""
    app = FastAPI()
    app.include_router(health_router)
    return TestClient(app)


def test_health_endpoint_healthy_status(client):
    """Test health endpoint returns 200 when service is healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert len(response.text) > 0
    # ...output should be kept short (only the first 4096 bytes are stored currently)
    # See: https://docs.docker.com/reference/dockerfile/#healthcheck
    assert len(response.text) < 4000
    health_resp = HealthResponse.model_validate(response.json())
    assert health_resp.status == HealthStatus.HEALTHY

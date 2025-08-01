"""Tests for health endpoints."""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.metrics.health import HealthService


@pytest.fixture
def healthy_service():
    """Create healthy service instance."""
    svc = HealthService()
    mock_health_checker_1 = Mock()
    mock_health_checker_1.check.return_value = True
    mock_health_checker_2 = Mock()
    mock_health_checker_2.check.return_value = True
    svc.add_checker(mock_health_checker_1, "svc_1")
    svc.add_checker(mock_health_checker_2, "svc_2")
    return svc


@pytest.fixture
def degraded_service():
    """Create degraded service instance."""
    svc = HealthService()
    mock_health_checker_1 = Mock()
    mock_health_checker_1.check.return_value = True
    mock_health_checker_2 = Mock()
    mock_health_checker_2.check.return_value = False
    svc.add_checker(mock_health_checker_1, "svc_1")
    svc.add_checker(mock_health_checker_2, "svc_2")
    return svc


@pytest.fixture
def fastapi_client_factory():
    """Factory fixture to create FastAPI client with any service."""

    def _create_client(service):
        app = FastAPI()
        app.include_router(service.router)
        return TestClient(app)

    return _create_client


def test_health_endpoint_healthy_status(fastapi_client_factory, healthy_service):
    """Test health endpoint returns 200 when service is healthy."""
    client = fastapi_client_factory(healthy_service)
    response = client.get("/health")
    assert response.json() == {"svc_1": True, "svc_2": True}
    assert response.status_code == 200


def test_health_endpoint_degraded_status(fastapi_client_factory, degraded_service):
    """Test health endpoint returns 503 when service is degraded."""
    client = fastapi_client_factory(degraded_service)
    response = client.get("/health")
    assert response.json() == {"svc_1": True, "svc_2": False}
    assert response.status_code == 503

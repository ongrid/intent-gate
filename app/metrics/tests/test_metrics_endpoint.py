"""Tests for health endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.metrics.metrics import metrics, metrics_router


@pytest.fixture
def client():
    """Create test client."""
    app = FastAPI()
    app.include_router(metrics_router)
    return TestClient(app)


def test_metrics_endpoint(client):
    """Test metrics endpoint returns data in prometheus exposition format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert len(response.text) > 0


def test_metrics_custom_metrics_exist(client):
    """Test that custom metrics defined in Metrics class are exposed."""
    response = client.get("/metrics")
    metrics_text = response.text
    # Assert our custom metrics are present in the output
    assert "rfqs_total" in metrics_text, "rfqs_total metric should be exposed"
    assert "rfqs_waiting" in metrics_text, "rfqs_waiting metric should be exposed"

    # Assert metric help text is present
    assert "Total number of RFQs processed" in metrics_text
    assert "Number of RFQs (Quotes) waiting to be settled" in metrics_text

    # Assert metric types are correct
    assert "# TYPE rfqs_total counter" in metrics_text
    assert "# TYPE rfqs_waiting gauge" in metrics_text


def test_metrics_with_sample_data(client):
    """Test metrics endpoint with sample data recorded."""
    # Record some sample metrics data
    metrics.rfqs_total.labels(
        chain_id="1",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x456",
        status="processed",
    ).inc()
    metrics.rfqs_waiting.labels(
        chain_id="1", solver="test_solver", base_token="0x123", quote_token="0x456"
    ).set(5)

    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    # Assert that our recorded data appears in the metrics
    assert (
        'rfqs_total{base_token="0x123",chain_id="1",quote_token="0x456",solver="test_solver",status="processed"} 1.0'
        in metrics_text
    )
    assert (
        'rfqs_waiting{base_token="0x123",chain_id="1",quote_token="0x456",solver="test_solver"} 5.0'
        in metrics_text
    )

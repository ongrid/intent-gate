"""Tests for health checker."""

from unittest.mock import patch

import pytest
from prometheus_client import CollectorRegistry, Counter

from app.metrics.health import CounterHealthChecker


@pytest.fixture
def mock_time():
    """Fixture to mock time.time() for testing time-based behavior."""
    with patch("time.time") as mock_time_func:
        # Start at a fixed timestamp
        mock_time_func.return_value = 1754000000.0
        yield mock_time_func


@pytest.fixture
def metrics_counter():
    """Create fresh metrics instance with custom registry to avoid state pollution."""
    custom_registry = CollectorRegistry()
    counter = Counter(
        "rfqs_total",
        "Total number of RFQs processed",
        ["chain_id", "solver", "base_token", "quote_token", "status"],
        registry=custom_registry,
    )
    return counter


def test_metrics_healthchecker_empty(metrics_counter):
    hc = CounterHealthChecker(
        metrics_counter, interval=10, label_values=["QUOTE_SENT"], label_key="status"
    )
    assert hc.check() is False


def test_metrics_healthchecker_with_data(metrics_counter, mock_time):
    start_time = 1754000000.0
    mock_time.return_value = start_time
    hc = CounterHealthChecker(
        metrics_counter, interval=10, label_values=["QUOTE_SENT"], label_key="status"
    )
    assert hc.check() is False
    # Unhealthy metrics data don't make service healthy
    metrics_counter.labels(
        chain_id="1",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x456",
        status="UNHEALTHY_STATUS",
    ).inc()
    assert hc.check() is False
    # Unhealthy metrics data don't make service healthy
    metrics_counter.labels(
        chain_id="2",
        solver="test_solver2",
        base_token="0x345",
        quote_token="0x456",
        status="UNHEALTHY_STATUS",
    ).inc()
    assert hc.check() is False
    # Record healthy record - this should make service healthy
    metrics_counter.labels(
        chain_id="1",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x456",
        status="QUOTE_SENT",
    ).inc()
    assert hc.check() is True

    # Check that multiple calls return the same result
    assert hc.check() is True
    assert hc.check() is True
    assert hc.check() is True

    mock_time.return_value = start_time + hc.interval - 1
    # Still healthy before interval expires
    assert hc.check() is True
    mock_time.return_value = start_time + hc.interval
    # After interval, should re-evaluate
    assert hc.check() is False
    assert hc.check() is False
    assert hc.check() is False

    # unhealthy metric doesn't heal
    metrics_counter.labels(
        chain_id="1",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x456",
        status="BAD_STATUS",
    ).inc()
    assert hc.check() is False

    # Healthy metric - does heal (double_hit to the previously reported)
    metrics_counter.labels(
        chain_id="1",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x456",
        status="QUOTE_SENT",
    ).inc()
    assert hc.check() is True

    # time passes and invalidates health again
    mock_time.return_value += hc.interval + 1
    assert hc.check() is False

    # undealthy metric doesn't heal
    metrics_counter.labels(
        chain_id="1",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x457",
        status="UNHEALTHY",
    ).inc()
    assert hc.check() is False

    # Healthy metric - does heal (unique without double hit)
    metrics_counter.labels(
        chain_id="222",
        solver="test_solver",
        base_token="0x123",
        quote_token="0x456",
        status="QUOTE_SENT",
    ).inc()
    assert hc.check() is True

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest


class Metrics:  # pylint: disable=too-few-public-methods
    """Prometheus metrics singleton for quoter service"""

    # TODO: Add health monitoring getter function  # pylint: disable=fixme
    # See #30 https://github.com/ongrid/open-intent-gate/issues/30

    def __init__(self) -> None:
        self.rfqs_total = Counter(
            "rfqs_total",
            "Total number of RFQs processed",
            ["chain_id", "solver", "base_token", "quote_token", "status"],
        )

        self.rfqs_waiting = Gauge(
            "rfqs_waiting",
            "Number of RFQs (Quotes) waiting to be settled",
            ["chain_id", "solver", "base_token", "quote_token"],
        )


metrics = Metrics()
metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
async def get_metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

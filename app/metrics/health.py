import time
from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Response
from prometheus_client import Counter


class CounterHealthChecker:  # pylint: disable=too-few-public-methods
    """A health checker for Prometheus Counter metrics.
    This class checks if the counter metrics have been updated within a specified interval.
    If any of the specified label k-v pairs have been incremented, it considers the system healthy.
    """

    def __init__(
        self, counter: Counter, interval: int, label_values: List[str], label_key: str = "status"
    ) -> None:
        self.counter: Counter = counter
        self.interval: int = interval
        self.label_key: str = label_key
        self.label_values: List[str] = label_values
        self.last_values = defaultdict(int)
        self.last_check_ts = time.time()
        self.healthy = False

    def check(self) -> bool:
        """Check the health status based on the counter metrics."""
        current_ts = time.time()
        if self.healthy and current_ts < self.last_check_ts + self.interval:
            return self.healthy

        self.healthy = False
        for metric_family in self.counter.collect():
            for s in metric_family.samples:
                if s.name.endswith("_created"):
                    continue
                labels = s.labels
                key = tuple(sorted(labels.items()))
                if labels.get(self.label_key, "") not in self.label_values:
                    continue
                current_val = int(s.value)
                delta = current_val - self.last_values[key]
                if delta > 0:
                    self.healthy = True
                self.last_values[key] = current_val

        self.last_check_ts = current_ts
        return self.healthy


class HealthService:
    """A service to manage health checks for multiple CounterHealthCheckers."""

    def __init__(self) -> None:
        self.checkers: Dict[str, CounterHealthChecker] = {}
        self.router = APIRouter(tags=["health"])
        self.router.add_api_route(
            "/health", self.health_check, methods=["GET"], response_model=Dict[str, bool]
        )

    def add_checker(self, checker: CounterHealthChecker, name: str) -> None:
        """Add a health checker to the service."""
        self.checkers[name] = checker

    def check_all(self) -> Dict[str, bool]:
        """Check the health status of all registered checkers."""
        return {name: checker.check() for name, checker in self.checkers.items()}

    async def health_check(self, response: Response) -> Dict[str, bool]:
        """
        Get application health status.

        Returns:
            - 200: Service is healthy
            - 503: Service is degraded
        """
        checks_result = self.check_all()
        is_healthy = all(checks_result.values())
        if is_healthy:
            response.status_code = 200
        else:
            response.status_code = 503
        return checks_result

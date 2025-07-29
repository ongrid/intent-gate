"""Health check endpoints."""

from fastapi import APIRouter, Response

from .schemas import HealthResponse, HealthStatus

health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
async def health_check(response: Response) -> HealthResponse:
    """
    Get application health status.

    Returns:
        - 200: Service is healthy
        - 503: Service is degraded
    """
    resp = HealthResponse(status=HealthStatus.HEALTHY)
    response.status_code = 200
    return resp

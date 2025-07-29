from enum import Enum

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """Health endpoint response model. Keep it short
    since only the first 4096 bytes are stored currently in docker engine.
    See: https://docs.docker.com/reference/dockerfile/#healthcheck"""

    status: HealthStatus = Field(default=HealthStatus.HEALTHY)

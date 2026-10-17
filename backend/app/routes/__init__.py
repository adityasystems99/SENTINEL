from .telemetry import router as telemetry_router
from .incidents import router as incidents_router
from .health import router as health_router
from .demo import router as demo_router
from .projects import router as projects_router
from .radar import router as radar_router
from .validation import router as validation_router

__all__ = [
    "telemetry_router",
    "incidents_router",
    "health_router",
    "demo_router",
    "projects_router",
    "radar_router",
    "validation_router",
]


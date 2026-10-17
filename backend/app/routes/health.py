"""Health and system metrics endpoint."""
import time
from fastapi import APIRouter
from ..storage.memory_store import store

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """Health check endpoint reporting telemetry and incident volume."""
    return {
        "status": "healthy",
        "service": "SENTINEL Backend",
        "timestamp": time.time(),
        "total_events_stored": store.total_events,
        "total_incidents": len(store.list_incidents()),
    }

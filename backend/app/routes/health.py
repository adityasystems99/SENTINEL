"""Health and system metrics endpoint."""
import os
import time
from fastapi import APIRouter
from ..storage.memory_store import store

router = APIRouter(tags=["Health"])


@router.get("/health")
@router.get("/health/")
async def health_check():
    """Health check endpoint reporting telemetry and incident volume."""
    commit_sha = os.getenv("VERCEL_GIT_COMMIT_SHA", "unknown")
    return {
        "status": "healthy",
        "service": "SENTINEL Backend",
        "commit": commit_sha[:7] if commit_sha != "unknown" else "unknown",
        "commit_sha": commit_sha,
        "timestamp": time.time(),
        "total_events_stored": store.total_events,
        "total_incidents": len(store.list_incidents()),
    }

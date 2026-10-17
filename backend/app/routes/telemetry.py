"""Telemetry ingestion API routes."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..models.telemetry import (
    TelemetryEvent,
    IngestBatchRequest,
    IngestResponse,
    LogLevel,
)
from ..storage.memory_store import store

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_telemetry(payload: IngestBatchRequest):
    """Ingest a batch of telemetry events with automatic deduplication."""
    if not payload.events:
        raise HTTPException(status_code=400, detail="Batch cannot be empty")
    
    accepted, deduplicated = store.add_events(payload.events)
    return IngestResponse(
        status="success",
        received=len(payload.events),
        accepted=accepted,
        deduplicated=deduplicated,
    )

@router.post("/ingest/event", response_model=IngestResponse)
async def ingest_single_event(event: TelemetryEvent):
    """Ingest a single telemetry event."""
    accepted, deduplicated = store.add_events([event])
    return IngestResponse(
        status="success",
        received=1,
        accepted=accepted,
        deduplicated=deduplicated,
    )

@router.get("/events", response_model=List[TelemetryEvent])
async def get_events(
    service: Optional[str] = Query(None, description="Filter by service name"),
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    limit: int = Query(100, ge=1, le=500, description="Max events to return"),
):
    """Query ingested telemetry events with optional filters."""
    return store.get_events(service=service, level=level, trace_id=trace_id, limit=limit)

@router.delete("/events")
async def clear_events():
    """Clear all telemetry events and incidents (resets in-memory store)."""
    store.clear()
    return {"status": "cleared", "total_events": 0}

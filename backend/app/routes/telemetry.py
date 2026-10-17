"""Telemetry ingestion API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..config import settings
from ..models.telemetry import (
    TelemetryEvent,
    IngestBatchRequest,
    IngestResponse,
    LogLevel,
)
from ..storage.memory_store import store
from ..auth.security import UserContext, get_current_user
from ..auth.rate_limiter import check_rate_limit

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.post(
    "/ingest",
    response_model=IngestResponse,
    dependencies=[Depends(check_rate_limit(max_requests=settings.rate_limit_per_minute, route_scope="telemetry"))],
)
async def ingest_telemetry(payload: IngestBatchRequest, current_user: UserContext = Depends(get_current_user)):
    """Ingest a batch of telemetry events with automatic deduplication and batch size bounds."""
    if not payload.events:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch cannot be empty")
    
    if len(payload.events) > settings.max_telemetry_batch_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size {len(payload.events)} exceeds maximum allowed limit of {settings.max_telemetry_batch_size} events.",
        )

    accepted, deduplicated = store.add_events(payload.events)
    return IngestResponse(
        status="success",
        received=len(payload.events),
        accepted=accepted,
        deduplicated=deduplicated,
    )

@router.post(
    "/ingest/event",
    response_model=IngestResponse,
    dependencies=[Depends(check_rate_limit(max_requests=settings.rate_limit_per_minute, route_scope="telemetry"))],
)
async def ingest_single_event(event: TelemetryEvent, current_user: UserContext = Depends(get_current_user)):
    """Ingest a single telemetry event."""
    accepted, deduplicated = store.add_events([event])
    return IngestResponse(
        status="success",
        received=1,
        accepted=accepted,
        deduplicated=deduplicated,
    )

@router.post(
    "/otlp/v1/traces",
    dependencies=[Depends(check_rate_limit(max_requests=settings.rate_limit_per_minute, route_scope="otlp"))],
)
async def ingest_otlp_traces(payload: dict, current_user: UserContext = Depends(get_current_user)):
    """OpenTelemetry standard OTLP/HTTP trace receiver endpoint compatible with OTLPSpanExporter."""
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed OTLP payload: expected JSON object.",
        )

    from ..services.otlp_adapter import convert_otlp_traces_payload
    try:
        events = convert_otlp_traces_payload(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process OTLP payload: {str(e)}",
        )

    if not events:
        return {"partialSuccess": {"rejectedSpans": 0, "errorMessage": "No valid spans parsed from OTLP payload"}}

    accepted, deduplicated = store.add_events(events)
    return {
        "status": "success",
        "spans_received": len(events),
        "spans_accepted": accepted,
        "spans_deduplicated": deduplicated,
        "partialSuccess": {}
    }

@router.get("/events", response_model=List[TelemetryEvent])
async def get_events(
    service: Optional[str] = Query(None, description="Filter by service name"),
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    limit: int = Query(100, ge=1, le=500, description="Max events to return"),
    current_user: UserContext = Depends(get_current_user),
):
    """Query ingested telemetry events with optional filters."""
    return store.get_events(service=service, level=level, trace_id=trace_id, limit=limit)

@router.delete("/events")
async def clear_events(current_user: UserContext = Depends(get_current_user)):
    """Clear all telemetry events and incidents (resets in-memory store, requires authentication)."""
    store.clear()
    return {"status": "cleared", "total_events": 0}

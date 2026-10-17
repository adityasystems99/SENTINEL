"""Tests for telemetry ingestion, storage, and deduplication."""
import time
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from backend.app.storage.memory_store import MemoryTelemetryStore

def test_telemetry_store_ingestion_and_dedup():
    store = MemoryTelemetryStore()
    now = time.time()

    ev1 = TelemetryEvent(
        event_id="evt-1",
        timestamp=now,
        service="order-service",
        level=LogLevel.INFO,
        event_type=EventType.LOG,
        message="Created order",
        trace_id="tr-100",
        span_id="sp-1"
    )

    ev2_duplicate_id = TelemetryEvent(
        event_id="evt-1",
        timestamp=now,
        service="order-service",
        level=LogLevel.INFO,
        event_type=EventType.LOG,
        message="Created order",
        trace_id="tr-100",
        span_id="sp-1"
    )

    ev3_content_dup = TelemetryEvent(
        event_id="evt-2",
        timestamp=now,
        service="order-service",
        level=LogLevel.INFO,
        event_type=EventType.LOG,
        message="Created order",
        trace_id="tr-100",
        span_id="sp-1"
    )

    ev4_unique = TelemetryEvent(
        event_id="evt-3",
        timestamp=now + 1.0,
        service="payment-service",
        level=LogLevel.ERROR,
        event_type=EventType.LOG,
        message="Payment timeout",
        trace_id="tr-100",
        span_id="sp-2"
    )

    accepted, deduped = store.add_events([ev1, ev2_duplicate_id, ev3_content_dup, ev4_unique])
    assert accepted == 2
    assert deduped == 2
    assert store.total_events == 2

def test_telemetry_query_filters():
    store = MemoryTelemetryStore()
    now = time.time()

    events = [
        TelemetryEvent(service="auth", level=LogLevel.INFO, message="ok", timestamp=now, trace_id="tr-1"),
        TelemetryEvent(service="auth", level=LogLevel.ERROR, message="auth failed", timestamp=now + 1, trace_id="tr-1"),
        TelemetryEvent(service="orders", level=LogLevel.ERROR, message="order failed", timestamp=now + 2, trace_id="tr-2"),
    ]
    store.add_events(events)

    # Filter by service
    auth_events = store.get_events(service="auth")
    assert len(auth_events) == 2

    # Filter by level
    errors = store.get_events(level=LogLevel.ERROR)
    assert len(errors) == 2

    # Filter by trace_id
    tr2_events = store.get_events(trace_id="tr-2")
    assert len(tr2_events) == 1
    assert tr2_events[0].service == "orders"

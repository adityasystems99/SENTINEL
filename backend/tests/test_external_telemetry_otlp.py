"""Tests verifying Task 2: External OpenTelemetry (OTLP) Ingestion & Conversion.
Verifies:
1. Standard OTLP/HTTP JSON payloads (POST /v1/traces) are correctly parsed and stored.
2. Hexadecimal trace IDs, span IDs, and parent-child linkages are preserved.
3. Nanosecond timestamps are mapped to seconds and duration_ms.
4. HTTP and OTLP error codes and exception events map to appropriate LogLevels.
5. Attributes and unsupported OTLP fields (such as span links) are retained in metadata.
"""
import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.storage.memory_store import store
from backend.app.models.telemetry import LogLevel
from backend.app.services.otlp_adapter import convert_otlp_traces_payload

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store():
    store.clear()
    yield
    store.clear()


def test_standard_otlp_traces_ingestion_and_conversion():
    """Verify ingestion of a standard OTLP/HTTP JSON payload with 2 linked spans."""
    start_nano = 1729180000000000000
    end_nano_child = 1729180000045000000   # 45ms duration
    end_nano_parent = 1729180000185000000  # 185ms duration

    otlp_payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "billing-service"}},
                        {"key": "telemetry.sdk.language", "value": {"stringValue": "python"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "opentelemetry.instrumentation.fastapi"},
                        "spans": [
                            {
                                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                "spanId": "00f067aa0ba902b7",
                                "name": "HTTP POST /charges",
                                "kind": 1,
                                "startTimeUnixNano": str(start_nano),
                                "endTimeUnixNano": str(end_nano_parent),
                                "attributes": [
                                    {"key": "http.method", "value": {"stringValue": "POST"}},
                                    {"key": "http.status_code", "value": {"intValue": 500}},
                                ],
                                "status": {"code": 2, "message": "Internal Server Error"},
                                "links": [{"traceId": "11111111111111111111111111111111", "spanId": "2222222222222222"}],
                            },
                            {
                                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                "spanId": "5fb397be34d23b0f",
                                "parentSpanId": "00f067aa0ba902b7",
                                "name": "DB SELECT balance",
                                "kind": 3,
                                "startTimeUnixNano": str(start_nano + 5000000),
                                "endTimeUnixNano": str(end_nano_child),
                                "attributes": [
                                    {"key": "db.system", "value": {"stringValue": "postgresql"}},
                                ],
                                "events": [
                                    {
                                        "timeUnixNano": str(start_nano + 40000000),
                                        "name": "exception",
                                        "attributes": [
                                            {"key": "exception.type", "value": {"stringValue": "OperationalError"}},
                                            {"key": "exception.message", "value": {"stringValue": "connection to server was lost"}},
                                        ],
                                    }
                                ],
                                "status": {"code": 2},
                            },
                        ],
                    }
                ],
            }
        ]
    }

    resp = client.post("/api/telemetry/otlp/v1/traces", json=otlp_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["spans_received"] == 2
    assert data["spans_accepted"] == 2

    # Query ingested events from store
    events = store.get_events(trace_id="4bf92f3577b34da6a3ce929d0e0e4736")
    assert len(events) == 2

    parent_ev = next(e for e in events if e.span_id == "00f067aa0ba902b7")
    child_ev = next(e for e in events if e.span_id == "5fb397be34d23b0f")

    # 1. Service name mapped from resource.attributes["service.name"]
    assert parent_ev.service == "billing-service"
    assert child_ev.service == "billing-service"

    # 2. Parent-child relationship preserved
    assert parent_ev.parent_span_id is None
    assert child_ev.parent_span_id == "00f067aa0ba902b7"

    # 3. Durations computed accurately
    assert parent_ev.duration_ms == 185.0
    assert child_ev.duration_ms == 40.0

    # 4. Error levels and messages mapped
    assert parent_ev.level == LogLevel.CRITICAL
    assert parent_ev.status_code == 500
    assert "connection to server was lost" in child_ev.message
    assert child_ev.level == LogLevel.CRITICAL

    # 5. Unsupported OTLP links preserved in metadata
    assert "otlp_links" in parent_ev.metadata
    assert len(parent_ev.metadata["otlp_links"]) == 1


def test_empty_and_malformed_otlp_payload():
    """Verify that empty or malformed OTLP payloads return graceful responses without crashing."""
    resp = client.post("/api/telemetry/otlp/v1/traces", json={})
    assert resp.status_code == 200
    assert "partialSuccess" in resp.json()

    resp2 = client.post("/api/telemetry/otlp/v1/traces", json={"resourceSpans": []})
    assert resp2.status_code == 200
    assert "partialSuccess" in resp2.json()

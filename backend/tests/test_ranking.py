"""Tests for NetworkX root cause ranking algorithm."""
import time
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from backend.app.graph.builder import build_incident_graph
from backend.app.graph.ranker import rank_root_causes

def test_root_cause_ranking_identifies_root_trigger():
    now = time.time()
    # Cascade: db failure in inventory -> order service error -> gateway 500
    events = [
        TelemetryEvent(
            event_id="e-db",
            timestamp=now,
            service="inventory-db",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="Connection pool exhausted",
            trace_id="tr-test",
            span_id="sp-db",
            parent_span_id="sp-order"
        ),
        TelemetryEvent(
            event_id="e-order",
            timestamp=now + 0.1,
            service="order-service",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="Inventory reservation failed: timeout",
            trace_id="tr-test",
            span_id="sp-order",
            parent_span_id="sp-gw"
        ),
        TelemetryEvent(
            event_id="e-gw",
            timestamp=now + 0.2,
            service="web-gateway",
            level=LogLevel.ERROR,
            event_type=EventType.TRACE,
            message="HTTP 500 returned to client",
            trace_id="tr-test",
            span_id="sp-gw"
        )
    ]

    G, nodes, _ = build_incident_graph(events)
    ranked = rank_root_causes(G, nodes)

    assert len(ranked) == 3
    # The primary trigger (e-db) must be ranked first
    assert ranked[0].node_id == "e-db"
    assert ranked[0].service == "inventory-db"
    assert ranked[0].score >= ranked[1].score
    assert ranked[0].confidence in ("HIGH", "MEDIUM")

def test_root_cause_ranking_with_bad_deployment():
    now = time.time()
    events = [
        TelemetryEvent(
            event_id="e-deploy",
            timestamp=now - 5.0,
            service="auth-service",
            level=LogLevel.INFO,
            event_type=EventType.DEPLOYMENT,
            message="Deployed release v2.4.1",
        ),
        TelemetryEvent(
            event_id="e-npe",
            timestamp=now,
            service="auth-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="NullPointer in TokenValidator",
        ),
        TelemetryEvent(
            event_id="e-gw-err",
            timestamp=now + 0.05,
            service="web-gateway",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="Auth check failed",
        ),
    ]

    G, nodes, _ = build_incident_graph(events)
    ranked = rank_root_causes(G, nodes)

    assert len(ranked) >= 2
    # auth-service (either the deployment or the npe error) should be top
    top_suspect = ranked[0]
    assert top_suspect.service == "auth-service"

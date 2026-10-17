"""Tests for NetworkX incident graph construction."""
import time
import networkx as nx
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from backend.app.graph.builder import build_incident_graph

def test_build_incident_graph_trace_hierarchy():
    now = time.time()
    events = [
        TelemetryEvent(
            event_id="e1",
            timestamp=now,
            service="gateway",
            level=LogLevel.INFO,
            event_type=EventType.TRACE,
            message="request started",
            trace_id="tr-1",
            span_id="sp-root"
        ),
        TelemetryEvent(
            event_id="e2",
            timestamp=now + 0.1,
            service="auth",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="unauthorized token",
            trace_id="tr-1",
            span_id="sp-child",
            parent_span_id="sp-root"
        ),
    ]

    G, nodes, edges = build_incident_graph(events)
    assert len(nodes) == 2
    assert G.number_of_nodes() == 2
    assert G.has_edge("e1", "e2")
    assert G["e1"]["e2"]["relation"] == "calls"

def test_build_incident_graph_deployment_correlation():
    now = time.time()
    deploy_event = TelemetryEvent(
        event_id="dep-1",
        timestamp=now - 2.0,
        service="inventory",
        level=LogLevel.INFO,
        event_type=EventType.DEPLOYMENT,
        message="Deployed v2.0",
    )
    error_event = TelemetryEvent(
        event_id="err-1",
        timestamp=now,
        service="inventory",
        level=LogLevel.CRITICAL,
        event_type=EventType.LOG,
        message="Fatal database connection timeout",
    )

    G, nodes, edges = build_incident_graph([deploy_event, error_event])
    assert G.has_edge("dep-1", "err-1")
    assert G["dep-1"]["err-1"]["relation"] == "deployed_before_error"

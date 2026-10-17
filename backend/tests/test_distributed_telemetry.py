"""Tests verifying Task 2: Network-Based Trace Propagation across independent HTTP services.
Verifies:
1. Real service-to-service communication over TCP sockets.
2. Trace ID consistency across request boundaries.
3. Accurate parent-child span linking (X-Trace-Id / W3C traceparent).
4. Failure cascade correlation and root-cause distinction.
5. Detection and honest handling of broken trace relationships.
"""
import time
import httpx
import pytest
from backend.app.graph.builder import build_incident_graph
from backend.app.graph.ranker import rank_root_causes
from backend.app.storage.memory_store import store
from demo_app.distributed_services import (
    DistributedServer,
    GatewayServiceHandler,
    InventoryServiceHandler,
)


@pytest.fixture
def distributed_cluster():
    """Start independent local HTTP services on ephemeral TCP ports."""
    store.clear()

    # Downstream inventory service
    inventory_svc = DistributedServer(
        name="inventory-service",
        handler_cls=InventoryServiceHandler,
        port=0,
        telemetry_sink=lambda evs: store.add_events(evs),
    )
    inventory_svc.start()

    # Upstream gateway service
    gateway_svc = DistributedServer(
        name="web-gateway",
        handler_cls=GatewayServiceHandler,
        port=0,
        telemetry_sink=lambda evs: store.add_events(evs),
    )
    # Link gateway's downstream port to inventory service port
    gateway_svc.server.downstream_port = inventory_svc.port
    gateway_svc.start()

    yield gateway_svc, inventory_svc

    gateway_svc.stop()
    inventory_svc.stop()
    store.clear()


def test_network_distributed_trace_propagation_healthy(distributed_cluster):
    """Verify that healthy HTTP requests propagate trace context across network sockets."""
    gateway_svc, inventory_svc = distributed_cluster
    inventory_svc.server.db_pool_exhausted = False
    gateway_svc.server.break_trace_headers = False

    # Execute HTTP call over real TCP socket
    gw_url = f"http://127.0.0.1:{gateway_svc.port}/checkout"
    with httpx.Client(timeout=3.0) as client:
        resp = client.post(gw_url)

    assert resp.status_code == 200
    data = resp.json()
    trace_id = data["trace_id"]
    gw_span = data["gw_span"]
    downstream_resp = data["downstream_resp"]

    # Verify trace ID is consistent across service boundary
    assert downstream_resp["trace_id"] == trace_id
    assert downstream_resp["parent_span_id"] == gw_span

    # Verify telemetry events received by SENTINEL
    events = store.get_events(trace_id=trace_id)
    assert len(events) >= 2
    svc_names = set(e.service for e in events)
    assert "web-gateway" in svc_names
    assert "inventory-service" in svc_names

    # Verify graph links parent span to child span
    G, nodes, edges = build_incident_graph(events)
    assert len(nodes) >= 2
    # Standard call relationship exists
    assert any(e.relation == "calls" for e in edges)


def test_network_distributed_trace_failure_cascade(distributed_cluster):
    """Verify that a failure in the downstream service is correctly captured and ranked."""
    gateway_svc, inventory_svc = distributed_cluster
    inventory_svc.server.db_pool_exhausted = True
    gateway_svc.server.break_trace_headers = False

    # Send 3 failing requests over network socket
    gw_url = f"http://127.0.0.1:{gateway_svc.port}/checkout"
    with httpx.Client(timeout=4.0) as client:
        for _ in range(3):
            resp = client.post(gw_url)
            assert resp.status_code == 502

    events = store.get_events()
    assert len(events) >= 6

    # Verify causal graph construction
    G, nodes, edges = build_incident_graph(events)
    # Callee failure causes caller failure edge must exist
    causal_edges = [e for e in edges if e.relation == "causes_failure_in"]
    assert len(causal_edges) > 0, "Causal failure propagation edge must connect callee error to caller error"

    # Verify root cause ranking prioritizes upstream culprit over downstream symptom
    ranked = rank_root_causes(G, nodes)
    assert len(ranked) > 0
    top_suspect = ranked[0]
    assert top_suspect.service == "inventory-service", (
        f"Expected inventory-service as root cause, got {top_suspect.service}"
    )
    assert top_suspect.confidence in ("HIGH", "MEDIUM")


def test_network_distributed_broken_trace_detection(distributed_cluster):
    """Verify that broken or missing trace headers do NOT fabricate false parent-child links."""
    gateway_svc, inventory_svc = distributed_cluster
    inventory_svc.server.db_pool_exhausted = True
    # Break trace propagation (simulates proxy/middleware stripping headers)
    gateway_svc.server.break_trace_headers = True

    gw_url = f"http://127.0.0.1:{gateway_svc.port}/checkout"
    with httpx.Client(timeout=4.0) as client:
        resp = client.post(gw_url)
        assert resp.status_code == 502

    events = store.get_events()
    # Gateway and Inventory should have DIFFERENT trace IDs
    gw_events = [e for e in events if e.service == "web-gateway"]
    inv_events = [e for e in events if e.service == "inventory-service"]
    assert len(gw_events) >= 1
    assert len(inv_events) >= 1

    gw_trace = gw_events[0].trace_id
    inv_trace = inv_events[0].trace_id
    assert gw_trace != inv_trace, "Broken trace headers must result in distinct trace identifiers"

    # Verify graph does NOT fabricate a direct call hierarchy edge between unlinked spans
    G, nodes, edges = build_incident_graph(events)
    has_fabricated_edge = any(
        (e.source in [ev.event_id for ev in gw_events] and e.target in [ev.event_id for ev in inv_events] and e.relation == "calls")
        or (e.source in [ev.event_id for ev in inv_events] and e.target in [ev.event_id for ev in gw_events] and e.relation == "causes_failure_in")
        for e in edges
    )
    assert not has_fabricated_edge, "Graph must not fabricate edges when trace context is missing"

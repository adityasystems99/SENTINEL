"""Dependency and Impact Radar Analysis Engine (Feature 4).
Extends graph topology to services, service-to-service calls, traces, errors, and cascading blast radiuses.
Strictly relies on real telemetry trace spans or explicitly configured demo dependencies without fabricating relationships.
"""
import time
from typing import Dict, List, Set, Tuple
import networkx as nx

from ..models.impact import (
    ComponentHealthStatus,
    DependencyRelationship,
    ImpactReport,
    ImpactedComponent,
    ServiceTopologyEdge,
    ServiceTopologyNode,
)
from ..models.telemetry import LogLevel, TelemetryEvent
from ..storage.memory_store import store

# Explicitly configured baseline dependencies for the local demo architecture
# (caller -> callee)
DEMO_TOPOLOGY = [
    ("web-gateway", "auth-service", "gateway_authenticates_session"),
    ("web-gateway", "order-service", "gateway_routes_checkout"),
    ("order-service", "inventory-service", "order_reserves_inventory"),
    ("order-service", "payment-service", "order_charges_payment"),
]

SERVICE_TIERS = {
    "web-gateway": "Edge Gateway (Public API)",
    "auth-service": "Security & Identity",
    "order-service": "Core Business Domain",
    "inventory-service": "Stateful Resource / Database",
    "payment-service": "External Financial Integration",
}

def build_service_topology(
    window_seconds: int = 600,
    events: List[TelemetryEvent] = None
) -> Tuple[nx.DiGraph, List[ServiceTopologyNode], List[ServiceTopologyEdge]]:
    """Build directed service dependency graph from telemetry spans and explicit architecture."""
    if events is None:
        start_time = time.time() - window_seconds
        events = store.get_events(since_timestamp=start_time, limit=500)


    # Directed call graph: caller -> callee
    G = nx.DiGraph()

    # Pre-populate known demo services
    for svc, tier in SERVICE_TIERS.items():
        G.add_node(svc, tier=tier, error_count=0, total_requests=0)

    # Edge data tracker: (source, target) -> {call_count, error_count, traces, evidence_source}
    edge_tracker: Dict[Tuple[str, str], Dict] = {}

    # Initialize with explicitly configured demo architecture
    for caller, callee, relation in DEMO_TOPOLOGY:
        edge_tracker[(caller, callee)] = {
            "relation": relation,
            "call_count": 0,
            "error_count": 0,
            "traces": set(),
            "evidence_source": "configured_demo_topology",
        }
        G.add_edge(caller, callee, relation=relation)

    # Index spans to extract observed caller -> callee telemetry
    spans_by_id: Dict[str, TelemetryEvent] = {}
    for ev in events:
        if ev.span_id:
            spans_by_id[ev.span_id] = ev

        # Ensure service node exists
        if not G.has_node(ev.service):
            tier = SERVICE_TIERS.get(ev.service, "Application Service")
            G.add_node(ev.service, tier=tier, error_count=0, total_requests=0)

        # Track error counts
        if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            G.nodes[ev.service]["error_count"] = G.nodes[ev.service].get("error_count", 0) + 1
        G.nodes[ev.service]["total_requests"] = G.nodes[ev.service].get("total_requests", 0) + 1

    # Extract observed dependencies from parent-child trace spans
    for ev in events:
        if ev.parent_span_id and ev.parent_span_id in spans_by_id:
            parent_ev = spans_by_id[ev.parent_span_id]
            caller = parent_ev.service
            callee = ev.service

            if caller != callee:
                key = (caller, callee)
                if key not in edge_tracker:
                    edge_tracker[key] = {
                        "relation": "calls",
                        "call_count": 0,
                        "error_count": 0,
                        "traces": set(),
                        "evidence_source": "telemetry_trace_spans",
                    }
                
                info = edge_tracker[key]
                info["call_count"] += 1
                info["evidence_source"] = "telemetry_trace_spans"
                if ev.trace_id:
                    info["traces"].add(ev.trace_id)
                if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL) or parent_ev.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                    info["error_count"] += 1

                if not G.has_edge(caller, callee):
                    G.add_edge(caller, callee, relation="calls")

    # Construct nodes list
    nodes: List[ServiceTopologyNode] = []
    for svc in G.nodes():
        node_data = G.nodes[svc]
        errs = node_data.get("error_count", 0)
        status = ComponentHealthStatus.FAILING if errs > 0 else ComponentHealthStatus.HEALTHY
        nodes.append(ServiceTopologyNode(
            id=svc,
            service=svc,
            status=status,
            tier=node_data.get("tier", "service"),
            error_count=errs,
            total_requests=node_data.get("total_requests", 0),
        ))

    # Construct edges list
    edges: List[ServiceTopologyEdge] = []
    for (caller, callee), info in edge_tracker.items():
        edges.append(ServiceTopologyEdge(
            source=caller,
            target=callee,
            relation=info.get("relation", "calls"),
            call_count=info.get("call_count", 1),
            error_count=info.get("error_count", 0),
            evidence_source=info.get("evidence_source", "configured_demo_topology"),
            sample_traces=list(info.get("traces", []))[:5],
        ))

    return G, nodes, edges

def analyze_service_impact(
    suspected_component: str,
    window_seconds: int = 600,
    events: List[TelemetryEvent] = None
) -> ImpactReport:
    """Analyze blast radius, cascading impact, and investigation priorities for a suspected service."""
    G, nodes, edges = build_service_topology(window_seconds=window_seconds, events=events)

    if not G.has_node(suspected_component):
        # Gracefully handle component not yet observed
        G.add_node(suspected_component, tier="External / Target", error_count=0, total_requests=0)

    target_errors = G.nodes[suspected_component].get("error_count", 0)
    target_status = ComponentHealthStatus.FAILING if target_errors > 0 else ComponentHealthStatus.UNKNOWN

    impacted: List[ImpactedComponent] = []

    # 1. Add target itself as Priority 1
    impacted.append(ImpactedComponent(
        service=suspected_component,
        status=target_status,
        relationship=DependencyRelationship.TARGET,
        distance=0,
        error_count=target_errors,
        observed_failure=(target_errors > 0),
        reason=f"Suspected root point of failure. Emitted {target_errors} error events in current inspection window.",
        priority=1,
        recommended_action="Inspect logs and stack traces on target service to determine internal trigger.",
    ))

    # 2. Traverse upstream callers (dependents):
    # In call graph: Caller -> Callee.
    # If Callee fails, Caller is the dependent that suffers failure or degradation.
    # We reverse G to find all services that call into suspected_component.
    reversed_G = G.reverse()

    # Shortest paths from suspected_component to all its upstream callers
    dependency_paths: List[List[str]] = []

    try:
        lengths = nx.single_source_shortest_path_length(reversed_G, suspected_component)
        paths = nx.single_source_shortest_path(reversed_G, suspected_component)
    except Exception:
        lengths = {suspected_component: 0}
        paths = {suspected_component: [suspected_component]}

    for caller_service, distance in sorted(lengths.items(), key=lambda x: x[1]):
        if caller_service == suspected_component:
            continue

        caller_errors = G.nodes[caller_service].get("error_count", 0)
        path = paths[caller_service]
        dependency_paths.append(path)

        observed = caller_errors > 0
        status = ComponentHealthStatus.FAILING if observed else ComponentHealthStatus.AT_RISK

        if distance == 1:
            rel = DependencyRelationship.DIRECT_DEPENDENT
            if observed:
                reason = f"Direct caller of {suspected_component}. Observed {caller_errors} cascade error(s) during synchronous invocations."
                prio = 2
                action = f"Check timeout thresholds, fallback circuits, and upstream HTTP 500 error propagation in {caller_service}."
            else:
                reason = f"Direct caller of {suspected_component}. Synchronous calls are at risk of cascading failure or thread exhaustion."
                prio = 4
                action = f"Monitor response latency and circuit breaker status on {caller_service}."
        else:
            rel = DependencyRelationship.TRANSITIVE_DEPENDENT
            if observed:
                reason = f"Transitive caller via {' -> '.join(path)}. Observed {caller_errors} downstream failure(s) in active window."
                prio = 3
                action = f"Verify user-facing error responses and degradation graceful fallbacks on {caller_service}."
            else:
                reason = f"Transitive caller via {' -> '.join(path)}. In blast radius; may degrade if incident persists."
                prio = 5
                action = f"Ensure retries and caching are active on {caller_service}."

        impacted.append(ImpactedComponent(
            service=caller_service,
            status=status,
            relationship=rel,
            distance=distance,
            error_count=caller_errors,
            observed_failure=observed,
            reason=reason,
            priority=prio,
            recommended_action=action,
        ))

    # 3. Also inspect downstream dependencies (services called BY suspected_component)
    for downstream in G.successors(suspected_component):
        if not any(item.service == downstream for item in impacted):
            down_errors = G.nodes[downstream].get("error_count", 0)
            impacted.append(ImpactedComponent(
                service=downstream,
                status=ComponentHealthStatus.FAILING if down_errors > 0 else ComponentHealthStatus.HEALTHY,
                relationship=DependencyRelationship.DOWNSTREAM_DEPENDENCY,
                distance=1,
                error_count=down_errors,
                observed_failure=(down_errors > 0),
                reason=f"Downstream dependency called by {suspected_component}. Verify if failure originated further downstream.",
                priority=3 if down_errors > 0 else 6,
                recommended_action=f"Check if {downstream} is reporting errors or connection refused.",
            ))

    # Sort impacted components by priority ascending
    impacted.sort(key=lambda x: (x.priority, x.distance))

    # Compile supporting evidence
    supporting_evidence: List[str] = []
    for edge in edges:
        if edge.error_count > 0:
            supporting_evidence.append(
                f"Observed {edge.error_count} error cascade(s) across edge [{edge.source} -> {edge.target}] (Source: {edge.evidence_source})"
            )

    limitations = [
        "Topology is reconstructed from trace spans and configured microservice architecture; asynchronous messaging queues (e.g. Kafka/RabbitMQ) without distributed context propagation may not show direct links.",
        "Observed failures require active telemetry reporting; components with disabled logging appear 'at risk' rather than 'failing'.",
        "Static relationships do not account for external third-party outages unless captured by gateway error spans."
    ]

    steps = [
        f"1. Isolate {suspected_component} and inspect recent deployment releases or database connection limits.",
        f"2. Check {impacted[1].service if len(impacted) > 1 else 'immediate caller'} circuit breaker metrics to halt cascading traffic.",
        "3. Review telemetry trace waterfalls to determine whether latency or hard exceptions triggered caller timeouts.",
        "4. Validate whether downstream dependencies are responsive before restarting upstream instances."
    ]

    return ImpactReport(
        suspected_component=suspected_component,
        impacted_components=impacted,
        dependency_paths=dependency_paths,
        nodes=nodes,
        edges=edges,
        supporting_evidence=supporting_evidence,
        confidence=0.92 if supporting_evidence else 0.85,
        limitations=limitations,
        suggested_investigation_steps=steps,
        analyzed_at=time.time(),
    )

"""NetworkX-based incident graph constructor.
Builds directed acyclic/cyclic graphs linking trace spans, causal error propagation, and deployment events.
"""
from typing import Dict, List, Tuple
import networkx as nx
from ..models.telemetry import TelemetryEvent, LogLevel, EventType
from ..models.incident import GraphNode, GraphEdge

def build_incident_graph(events: List[TelemetryEvent]) -> Tuple[nx.DiGraph, List[GraphNode], List[GraphEdge]]:
    """Construct a NetworkX DiGraph from a set of correlated telemetry events."""
    G = nx.DiGraph()
    nodes_map: Dict[str, GraphNode] = {}
    edges_list: List[GraphEdge] = []

    # Sort events chronologically
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    # 1. Add all nodes to graph
    for ev in sorted_events:
        is_err = ev.level in (LogLevel.ERROR, LogLevel.CRITICAL)
        label = f"[{ev.service}] {ev.level.value}: {ev.message[:40]}"
        
        node = GraphNode(
            id=ev.event_id,
            label=label,
            service=ev.service,
            event_type=ev.event_type.value,
            level=ev.level,
            timestamp=ev.timestamp,
            is_error=is_err,
            message=ev.message,
            metadata=ev.metadata,
        )
        nodes_map[ev.event_id] = node
        
        G.add_node(
            ev.event_id,
            service=ev.service,
            level=ev.level.value,
            event_type=ev.event_type.value,
            timestamp=ev.timestamp,
            is_error=is_err,
            message=ev.message,
            trace_id=ev.trace_id,
            span_id=ev.span_id,
        )

    # Index events by trace_id and span_id for hierarchy construction
    spans_by_id: Dict[str, TelemetryEvent] = {}
    traces_map: Dict[str, List[TelemetryEvent]] = {}
    deployments: List[TelemetryEvent] = []

    for ev in sorted_events:
        if ev.span_id:
            spans_by_id[ev.span_id] = ev
        if ev.trace_id:
            traces_map.setdefault(ev.trace_id, []).append(ev)
        if ev.event_type == EventType.DEPLOYMENT:
            deployments.append(ev)

    # 2. Build edges based on trace hierarchy
    for ev in sorted_events:
        if ev.parent_span_id and ev.parent_span_id in spans_by_id:
            parent_event = spans_by_id[ev.parent_span_id]
            is_ev_err = ev.level in (LogLevel.ERROR, LogLevel.CRITICAL)
            is_parent_err = parent_event.level in (LogLevel.ERROR, LogLevel.CRITICAL)

            if is_ev_err and is_parent_err:
                # In failure causality: failing callee causes failure in caller
                if not G.has_edge(ev.event_id, parent_event.event_id):
                    G.add_edge(ev.event_id, parent_event.event_id, relation="causes_failure_in", weight=1.2)
                    edges_list.append(GraphEdge(
                        source=ev.event_id,
                        target=parent_event.event_id,
                        relation="causes_failure_in",
                        weight=1.2
                    ))
            else:
                # Standard call hierarchy: caller -> callee
                if not G.has_edge(parent_event.event_id, ev.event_id):
                    G.add_edge(parent_event.event_id, ev.event_id, relation="calls", weight=1.0)
                    edges_list.append(GraphEdge(
                        source=parent_event.event_id,
                        target=ev.event_id,
                        relation="calls",
                        weight=1.0
                    ))

    # 3. Build causal error propagation edges within identical traces (if not already linked)
    for trace_id, trace_events in traces_map.items():
        trace_events_sorted = sorted(trace_events, key=lambda e: e.timestamp)
        for i in range(len(trace_events_sorted) - 1):
            e1 = trace_events_sorted[i]
            e2 = trace_events_sorted[i + 1]
            if (e1.level in (LogLevel.ERROR, LogLevel.CRITICAL)) and (e2.level in (LogLevel.ERROR, LogLevel.CRITICAL)):
                # If neither direction exists, link earlier error to later error
                if not G.has_edge(e1.event_id, e2.event_id) and not G.has_edge(e2.event_id, e1.event_id):
                    G.add_edge(e1.event_id, e2.event_id, relation="propagates_to", weight=0.8)
                    edges_list.append(GraphEdge(
                        source=e1.event_id,
                        target=e2.event_id,
                        relation="propagates_to",
                        weight=0.8
                    ))

    # 4. Link deployment events to subsequent errors in the same or downstream services
    for dep in deployments:
        for ev in sorted_events:
            if ev.timestamp > dep.timestamp and (ev.timestamp - dep.timestamp) <= 300.0:
                if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                    # Link deployment to early errors
                    if not G.has_edge(dep.event_id, ev.event_id):
                        relation = "deployed_before_error" if dep.service == ev.service else "deployment_precedes"
                        weight = 1.2 if dep.service == ev.service else 0.5
                        G.add_edge(dep.event_id, ev.event_id, relation=relation, weight=weight)
                        edges_list.append(GraphEdge(
                            source=dep.event_id,
                            target=ev.event_id,
                            relation=relation,
                            weight=weight
                        ))

    # 5. Service-level fallback causal links (if disconnected components exist among errors)
    err_events = [e for e in sorted_events if e.level in (LogLevel.ERROR, LogLevel.CRITICAL)]
    for i in range(len(err_events) - 1):
        e1 = err_events[i]
        e2 = err_events[i + 1]
        time_diff = e2.timestamp - e1.timestamp
        if 0.0 <= time_diff <= 2.0 and e1.service != e2.service:
            if not G.has_edge(e1.event_id, e2.event_id) and not nx.has_path(G, e1.event_id, e2.event_id):
                G.add_edge(e1.event_id, e2.event_id, relation="temporal_cascade", weight=0.6)
                edges_list.append(GraphEdge(
                    source=e1.event_id,
                    target=e2.event_id,
                    relation="temporal_cascade",
                    weight=0.6
                ))

    return G, list(nodes_map.values()), edges_list

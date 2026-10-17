"""NetworkX-based Root Cause Ranking Engine.
Analyzes incident graph topology, causal directionality, and temporal sequencing.
"""
from typing import Dict, List
import networkx as nx
from ..models.incident import RootCauseCandidate, GraphNode

def rank_root_causes(G: nx.DiGraph, nodes: List[GraphNode]) -> List[RootCauseCandidate]:
    """Rank potential root causes using NetworkX graph analysis and anomaly heuristics."""
    if not G.nodes:
        return []

    node_dict = {n.id: n for n in nodes}
    candidates: List[RootCauseCandidate] = []

    # Strategy:
    # In a failure cascade, root causes act as sources (in-degree == 0 or low in-degree in causal graph)
    # and have high downstream fan-out (out-degree > 0).
    # Reversing the graph allows PageRank to propagate importance backward from downstream symptoms
    # to the primary upstream root causes.

    reversed_G = G.reverse(copy=True)
    
    # 1. Base topological importance via PageRank on reversed graph
    try:
        # Personalize PageRank toward error and deployment nodes
        personalization = {}
        for nid in reversed_G.nodes:
            n_data = reversed_G.nodes[nid]
            if n_data.get("is_error"):
                personalization[nid] = 2.0
            elif n_data.get("event_type") == "deployment":
                personalization[nid] = 3.0
            else:
                personalization[nid] = 0.5

        # Normalize personalization
        total_p = sum(personalization.values())
        personalization = {k: v / total_p for k, v in personalization.items()}

        pagerank_scores = nx.pagerank(
            reversed_G,
            alpha=0.85,
            personalization=personalization,
            weight="weight",
            max_iter=200
        )
    except Exception:
        # Fallback if convergence fails on complex/disconnected graphs
        degree_sum = max(1, sum(dict(reversed_G.in_degree()).values()))
        pagerank_scores = {nid: reversed_G.in_degree(nid) / degree_sum for nid in reversed_G.nodes}

    # 2. Compute composite causality score combining topology, time, and severity
    all_timestamps = [n.timestamp for n in nodes]
    min_time = min(all_timestamps) if all_timestamps else 0.0
    max_time = max(all_timestamps) if all_timestamps else 1.0
    time_span = max(1.0, max_time - min_time)

    scored_nodes: List[tuple[str, float, List[str]]] = []

    for nid in G.nodes:
        n = node_dict.get(nid)
        if not n:
            continue

        reasons = []
        base_pr = pagerank_scores.get(nid, 0.0)
        score = base_pr * 1.5

        # Factor A: In-degree vs Out-degree in original graph
        in_deg = G.in_degree(nid)
        out_deg = G.out_degree(nid)

        if in_deg == 0 and out_deg > 0:
            score += 0.35
            reasons.append(f"Root source in causal chain with {out_deg} downstream impact(s)")
        elif out_deg > in_deg:
            score += 0.20
            reasons.append(f"High outbound blast radius ({out_deg} downstream nodes)")

        # Factor B: Temporal precedence (earlier events in incident are more likely causes)
        time_offset = n.timestamp - min_time
        temporal_priority = 1.0 - (time_offset / time_span)  # 1.0 for first event, 0.0 for last
        score += temporal_priority * 0.25
        if temporal_priority > 0.8:
            reasons.append("Occurred in initial trigger window of the incident")

        # Factor C: Deployment marker preceding errors
        if n.event_type == "deployment":
            score += 0.40
            reasons.append(f"Code deployment event on [{n.service}] immediately preceding failures")

        # Factor D: Error severity
        if n.is_error:
            score += 0.20
            reasons.append(f"Direct error/exception on [{n.service}]")

        scored_nodes.append((nid, score, reasons))

    # Sort descending by score
    scored_nodes.sort(key=lambda x: x[1], reverse=True)

    # Normalize top score to scale between 0.0 and 1.0
    max_score = scored_nodes[0][1] if scored_nodes else 1.0

    for nid, raw_score, reasons in scored_nodes:
        n = node_dict[nid]
        normalized_score = min(1.0, max(0.05, round(raw_score / max_score, 3)))
        
        in_deg = G.in_degree(nid)
        out_deg = G.out_degree(nid)
        out_edges = G.out_edges(nid, data=True)
        verified_causal_edges = [
            (u, v, d) for u, v, d in out_edges
            if d.get("relation") in ("causes_failure_in", "deployed_before_error")
        ]
        has_causal_edge = len(verified_causal_edges) > 0
        has_deployment = (n.event_type == "deployment")
        is_isolated = (in_deg == 0 and out_deg == 0)
        has_only_temporal_fallback = (out_deg > 0 and len(verified_causal_edges) == 0 and not has_deployment)

        if (is_isolated or has_only_temporal_fallback) and not has_deployment:
            # Isolated node or weak temporal fallback without trace linkage is inherently low confidence
            confidence = "LOW"
            reasons.append("Speculative correlation without trace hierarchy (inconclusive evidence)")
        elif not has_causal_edge and not has_deployment and normalized_score >= 0.75:
            # Without causal fan-out or deployment evidence, cap confidence at MEDIUM
            confidence = "MEDIUM"
        elif normalized_score >= 0.75:
            confidence = "HIGH"
        elif normalized_score >= 0.45:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        candidates.append(RootCauseCandidate(
            node_id=nid,
            service=n.service,
            score=normalized_score,
            confidence=confidence,
            event_type=n.event_type,
            message=n.message,
            timestamp=n.timestamp,
            reasons=reasons or ["Associated node in incident cascade"]
        ))

    return candidates

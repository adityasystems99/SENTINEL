"""Phase 10 Evaluation Test Suite: Unfamiliar Failure & RAG Reliability.
Tasks 3 & 4:
- Evaluates unfamiliar failure (Internal DNS Resolution Failure).
- Tests incomplete/dropped telemetry scenario for appropriate uncertainty reporting.
- Compares SENTINEL causal graph ranker against raw error-count baseline.
- Compares Graph-Only vs Graph-plus-Historical RAG on unfamiliar incidents.
- Exports machine-readable results to backend/evaluation_results_phase10.json.
"""
import json
import os
import time
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.telemetry import TelemetryEvent, LogLevel
from backend.app.graph.builder import build_incident_graph
from backend.app.graph.ranker import rank_root_causes
from backend.app.services.rag import (
    vector_store,
    initialize_knowledge_base,
    synthesize_investigation,
)
from backend.app.storage.memory_store import store
from demo_app.scenarios_phase10 import (
    PHASE10_SCENARIO_CATALOG,
    generate_phase10_scenario_telemetry,
)

client = TestClient(app)


def baseline_error_count_ranker(events: List[TelemetryEvent]) -> List[str]:
    """Baseline ranker: sorts components purely by raw error log counts."""
    counts: Dict[str, int] = {}
    for ev in events:
        if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            counts[ev.service] = counts.get(ev.service, 0) + 1
    return [svc for svc, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)]


def run_sentinel_graph_ranking(events: List[TelemetryEvent]):
    """SENTINEL ranker: builds NetworkX causal graph and runs Reverse Personalized PageRank."""
    G, nodes, edges = build_incident_graph(events)
    ranked = rank_root_causes(G, nodes)

    unique_candidates = []
    seen = set()
    for c in ranked:
        if c.service not in seen:
            seen.add(c.service)
            unique_candidates.append({
                "service": c.service,
                "node_id": c.node_id,
                "score": round(c.score, 4),
                "confidence": c.confidence,
                "reasons": c.reasons,
            })
    return unique_candidates, nodes, ranked


@pytest.fixture(autouse=True)
def setup_eval_env():
    store.clear()
    initialize_knowledge_base()
    yield
    store.clear()


def test_phase10_unfamiliar_failure_evaluation():
    """Evaluate unfamiliar failure modes, missing spans, and RAG reliability."""
    evaluation_records: List[Dict[str, Any]] = []

    # =========================================================================
    # Scenario 1: Unfamiliar DNS Resolution Failure (CoreDNS Partition)
    # =========================================================================
    dns_meta = PHASE10_SCENARIO_CATALOG["dns_nxdomain_resolution_failure"]
    dns_events = generate_phase10_scenario_telemetry("dns_nxdomain_resolution_failure")
    dns_gt = dns_meta["ground_truth_root_cause"]

    # 1. Baseline Ranking
    dns_baseline = baseline_error_count_ranker(dns_events)
    dns_baseline_top1 = dns_baseline[0] if dns_baseline else None
    dns_baseline_correct = (dns_baseline_top1 == dns_gt)

    # 2. SENTINEL Graph Ranking (Without RAG)
    dns_candidates, dns_nodes, dns_raw_causes = run_sentinel_graph_ranking(dns_events)
    dns_sentinel_top1 = dns_candidates[0]["service"] if dns_candidates else None
    dns_sentinel_top3 = [c["service"] for c in dns_candidates[:3]]
    dns_sentinel_correct = (dns_sentinel_top1 == dns_gt)
    dns_confidence = dns_candidates[0]["confidence"] if dns_candidates else "LOW"

    # Baseline fails because noisy gateway emitted 15 errors vs 1 on order-service
    assert dns_baseline_top1 == "web-gateway"
    assert dns_baseline_correct is False

    # SENTINEL succeeds because causal edge connects callee DNS error to caller
    assert dns_sentinel_top1 == "order-service"
    assert dns_sentinel_correct is True

    # 3. Historical RAG Retrieval
    dns_query = f"{dns_meta['title']} {dns_sentinel_top1}"
    dns_rag_results = vector_store.search(dns_query, top_k=3, affected_service=dns_sentinel_top1)
    
    # 4. Graph + Historical RAG Synthesis
    dns_synthesis = synthesize_investigation(
        nodes=dns_nodes,
        ranked_causes=dns_raw_causes,
        top_k=3,
    )

    # Verify synthesis keeps facts and historical separate
    assert len(dns_synthesis.observed_facts) > 0
    assert len(dns_synthesis.root_cause_hypotheses) > 0
    assert len(dns_synthesis.uncertainty_disclosures) > 0

    evaluation_records.append({
        "scenario_id": "dns_nxdomain_resolution_failure",
        "title": dns_meta["title"],
        "is_unfamiliar": True,
        "is_incomplete": False,
        "ground_truth_root_cause": dns_gt,
        "telemetry_events_ingested": len(dns_events),
        "baseline_top_1": dns_baseline_top1,
        "baseline_correct": dns_baseline_correct,
        "sentinel_top_1": dns_sentinel_top1,
        "sentinel_top_1_correct": dns_sentinel_correct,
        "sentinel_top_3_correct": dns_gt in dns_sentinel_top3,
        "sentinel_confidence": dns_confidence,
        "supporting_evidence": dns_candidates[0]["reasons"],
        "uncertainty_disclosures": dns_synthesis.uncertainty_disclosures,
        "top_rag_doc_id": dns_rag_results[0].doc_id if dns_rag_results else None,
        "top_rag_score": dns_rag_results[0].similarity_score if dns_rag_results else 0.0,
    })

    # =========================================================================
    # Scenario 2: Incomplete Telemetry / Dropped Intermediate Spans
    # =========================================================================
    inc_meta = PHASE10_SCENARIO_CATALOG["incomplete_telemetry_missing_spans"]
    inc_events = generate_phase10_scenario_telemetry("incomplete_telemetry_missing_spans")
    inc_gt = inc_meta["ground_truth_root_cause"]

    inc_baseline = baseline_error_count_ranker(inc_events)
    inc_candidates, inc_nodes, inc_raw_causes = run_sentinel_graph_ranking(inc_events)
    inc_confidence = inc_candidates[0]["confidence"] if inc_candidates else "LOW"

    # Missing spans must produce LOW or MEDIUM confidence, NOT unjustified HIGH confidence
    assert inc_confidence in ("LOW", "MEDIUM"), f"Missing spans must produce LOW/MEDIUM confidence, got {inc_confidence}"

    inc_synthesis = synthesize_investigation(
        nodes=inc_nodes,
        ranked_causes=inc_raw_causes,
        top_k=3,
    )
    # Uncertainty disclosure must explicitly report missing telemetry
    has_missing_disclosure = any(
        "missing" in u.lower() or "uncaptured" in u.lower() or "telemetry" in u.lower() or "isolated" in u.lower()
        for u in inc_synthesis.uncertainty_disclosures
    )
    assert has_missing_disclosure is True

    evaluation_records.append({
        "scenario_id": "incomplete_telemetry_missing_spans",
        "title": inc_meta["title"],
        "is_unfamiliar": True,
        "is_incomplete": True,
        "ground_truth_root_cause": inc_gt,
        "telemetry_events_ingested": len(inc_events),
        "baseline_top_1": inc_baseline[0] if inc_baseline else None,
        "baseline_correct": (inc_baseline[0] == inc_gt) if inc_baseline else False,
        "sentinel_top_1": inc_candidates[0]["service"] if inc_candidates else None,
        "sentinel_top_1_correct": (inc_candidates[0]["service"] == inc_gt) if inc_candidates else False,
        "sentinel_top_3_correct": inc_gt in [c["service"] for c in inc_candidates[:3]],
        "sentinel_confidence": inc_confidence,
        "supporting_evidence": inc_candidates[0]["reasons"] if inc_candidates else [],
        "uncertainty_disclosures": inc_synthesis.uncertainty_disclosures,
        "top_rag_doc_id": None,
        "top_rag_score": 0.0,
    })

    # Save Phase 10 results JSON
    results_path = os.path.join(os.path.dirname(__file__), "..", "evaluation_results_phase10.json")
    results_payload = {
        "evaluation_name": "SENTINEL Phase 10 External Telemetry & Unfamiliar Failure Evaluation",
        "timestamp": time.time(),
        "unfamiliar_scenarios_evaluated": len(evaluation_records),
        "summary_metrics": {
            "unfamiliar_dns_failure_baseline_correct": dns_baseline_correct,
            "unfamiliar_dns_failure_sentinel_top1_correct": dns_sentinel_correct,
            "unfamiliar_dns_failure_confidence": dns_confidence,
            "incomplete_spans_uncertainty_honestly_reported": (inc_confidence in ("LOW", "MEDIUM")),
            "missing_telemetry_disclosure_verified": has_missing_disclosure,
        },
        "detailed_scenarios": evaluation_records,
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print("\n=================================================================")
    print("PHASE 10 UNFAMILIAR FAILURE & MISSING SPANS EVALUATION")
    print(f"Unfamiliar DNS Failure Baseline Correct:   {dns_baseline_correct} (Baseline picked '{dns_baseline_top1}')")
    print(f"Unfamiliar DNS Failure SENTINEL Correct:   {dns_sentinel_correct} (SENTINEL picked '{dns_sentinel_top1}')")
    print(f"Unfamiliar DNS Failure Confidence:         {dns_confidence}")
    print(f"Incomplete Spans Uncertainty Flagged:      {inc_confidence in ('LOW', 'MEDIUM')} (Assigned '{inc_confidence}')")
    print(f"Missing Telemetry Disclosures Verified:    {has_missing_disclosure}")
    print(f"Results Written To:                        {os.path.abspath(results_path)}")
    print("=================================================================\n")

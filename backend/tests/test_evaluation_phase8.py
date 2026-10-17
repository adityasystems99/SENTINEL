"""SENTINEL Phase 8 — Real-World Incident Evaluation & Hardening Suite.

Evaluates SENTINEL's causal graph ranking and historical incident RAG against
an instrumented demo application emitting realistic telemetry across microservices.

Generates a machine-readable evaluation results file at:
backend/evaluation_results_phase8.json
"""
import json
import os
import time
from typing import Dict, List, Any, Optional
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from backend.app.graph.builder import build_incident_graph
from backend.app.graph.ranker import rank_root_causes
from backend.app.services.rag import vector_store, initialize_knowledge_base, synthesize_investigation
from backend.app.storage.memory_store import store
from demo_app.service import DemoAppService
from demo_app.scenarios import (
    SCENARIO_CATALOG,
    inject_db_pool_exhaustion,
    inject_bad_auth_deployment,
    inject_payment_timeout,
    generate_healthy_traffic,
    recover_all,
)

client = TestClient(app)

def baseline_error_count_ranker(events: List[TelemetryEvent]) -> List[str]:
    """Transparent baseline ranker: ranks services purely by raw error log count."""
    counts: Dict[str, int] = {}
    for ev in events:
        if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            counts[ev.service] = counts.get(ev.service, 0) + 1
    return [svc for svc, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)]


def run_sentinel_graph_ranking(events: List[TelemetryEvent]):
    """Runs SENTINEL's NetworkX causal graph + Personalized PageRank root-cause ranker."""
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
def reset_environment():
    """Ensure clean telemetry and indexed RAG store before each evaluation test."""
    store.clear()
    client.post("/api/demo/scenario/recover")
    client.post("/api/rag/ingest")
    yield
    store.clear()
    client.post("/api/demo/scenario/recover")


def test_phase8_comprehensive_real_world_evaluation():
    """Execute evaluation across all reproducible scenarios using real emitted telemetry."""
    evaluation_records: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Scenario 1: Database Connection Pool Exhaustion (Real Demo App Telemetry)
    # -------------------------------------------------------------------------
    store.clear()
    demo = DemoAppService(telemetry_sink=lambda evs: store.add_events(evs))
    inject_db_pool_exhaustion(demo, count=4)
    scen1_events = store.get_events()
    assert len(scen1_events) >= 12  # 3 spans per checkout * 4 requests

    # 1. Baseline Ranker
    scen1_baseline = baseline_error_count_ranker(scen1_events)

    # 2. SENTINEL Graph Ranker
    scen1_sentinel, scen1_nodes, scen1_raw_causes = run_sentinel_graph_ranking(scen1_events)
    scen1_gt = SCENARIO_CATALOG["db_pool_exhaustion"]["ground_truth_root_cause"]
    scen1_sentinel_top = scen1_sentinel[0]["service"] if scen1_sentinel else None
    scen1_sentinel_top3 = [c["service"] for c in scen1_sentinel[:3]]

    # 3. Historical RAG Retrieval
    query_text_1 = "HikariPool connection pool saturation timeout on inventory service"
    rag_res_1 = vector_store.search(query_text_1, top_k=3, affected_service=scen1_gt)
    top_rag_1 = rag_res_1[0] if rag_res_1 else None

    # Synthesis check: does synthesis keep evidence separate from historical docs?
    synthesis_1 = synthesize_investigation(
        nodes=scen1_nodes,
        ranked_causes=scen1_raw_causes,
        top_k=3,
    )
    assert len(synthesis_1.observed_facts) > 0
    assert len(synthesis_1.root_cause_hypotheses) > 0
    assert len(synthesis_1.historical_evidence) > 0
    assert len(synthesis_1.uncertainty_disclosures) > 0

    evaluation_records.append({
        "scenario_id": "db_pool_exhaustion",
        "title": SCENARIO_CATALOG["db_pool_exhaustion"]["title"],
        "ground_truth_root_cause": scen1_gt,
        "telemetry_events_ingested": len(scen1_events),
        "baseline_top_1": scen1_baseline[0] if scen1_baseline else None,
        "baseline_correct": (scen1_baseline[0] == scen1_gt) if scen1_baseline else False,
        "sentinel_top_1": scen1_sentinel_top,
        "sentinel_top_1_correct": scen1_sentinel_top == scen1_gt,
        "sentinel_top_3_correct": scen1_gt in scen1_sentinel_top3,
        "sentinel_confidence": scen1_sentinel[0]["confidence"] if scen1_sentinel else "UNKNOWN",
        "top_rag_doc_id": top_rag_1.doc_id if top_rag_1 else None,
        "top_rag_similarity": top_rag_1.similarity_score if top_rag_1 else 0.0,
        "rag_relevant_match": (top_rag_1.doc_id in (SCENARIO_CATALOG["db_pool_exhaustion"]["historical_incident_id"], SCENARIO_CATALOG["db_pool_exhaustion"]["historical_runbook_id"])) if top_rag_1 else False,
        "supporting_evidence": scen1_sentinel[0]["reasons"] if scen1_sentinel else [],
    })

    # -------------------------------------------------------------------------
    # Scenario 2: Faulty Auth Service Deployment (Real Demo App Telemetry)
    # -------------------------------------------------------------------------
    store.clear()
    demo = DemoAppService(telemetry_sink=lambda evs: store.add_events(evs))
    inject_bad_auth_deployment(demo, count=4)
    scen2_events = store.get_events()
    assert len(scen2_events) >= 9  # 1 deployment + 2 events per checkout * 4 requests

    scen2_baseline = baseline_error_count_ranker(scen2_events)
    scen2_sentinel, _, _ = run_sentinel_graph_ranking(scen2_events)
    scen2_gt = SCENARIO_CATALOG["bad_auth_deployment"]["ground_truth_root_cause"]
    scen2_sentinel_top = scen2_sentinel[0]["service"] if scen2_sentinel else None
    scen2_sentinel_top3 = [c["service"] for c in scen2_sentinel[:3]]

    query_text_2 = "NullPointerDereference in TokenValidator.verify session token is None"
    rag_res_2 = vector_store.search(query_text_2, top_k=3, affected_service=scen2_gt)
    top_rag_2 = rag_res_2[0] if rag_res_2 else None

    evaluation_records.append({
        "scenario_id": "bad_auth_deployment",
        "title": SCENARIO_CATALOG["bad_auth_deployment"]["title"],
        "ground_truth_root_cause": scen2_gt,
        "telemetry_events_ingested": len(scen2_events),
        "baseline_top_1": scen2_baseline[0] if scen2_baseline else None,
        "baseline_correct": (scen2_baseline[0] == scen2_gt) if scen2_baseline else False,
        "sentinel_top_1": scen2_sentinel_top,
        "sentinel_top_1_correct": scen2_sentinel_top == scen2_gt,
        "sentinel_top_3_correct": scen2_gt in scen2_sentinel_top3,
        "sentinel_confidence": scen2_sentinel[0]["confidence"] if scen2_sentinel else "UNKNOWN",
        "top_rag_doc_id": top_rag_2.doc_id if top_rag_2 else None,
        "top_rag_similarity": top_rag_2.similarity_score if top_rag_2 else 0.0,
        "rag_relevant_match": (top_rag_2.doc_id in (SCENARIO_CATALOG["bad_auth_deployment"]["historical_incident_id"], SCENARIO_CATALOG["bad_auth_deployment"]["historical_runbook_id"])) if top_rag_2 else False,
        "supporting_evidence": scen2_sentinel[0]["reasons"] if scen2_sentinel else [],
    })

    # -------------------------------------------------------------------------
    # Scenario 3: Downstream Payment Timeout (Real Demo App Telemetry)
    # -------------------------------------------------------------------------
    store.clear()
    demo = DemoAppService(telemetry_sink=lambda evs: store.add_events(evs))
    inject_payment_timeout(demo, count=4)
    scen3_events = store.get_events()
    assert len(scen3_events) >= 16

    scen3_baseline = baseline_error_count_ranker(scen3_events)
    scen3_sentinel, _, _ = run_sentinel_graph_ranking(scen3_events)
    scen3_gt = SCENARIO_CATALOG["payment_timeout"]["ground_truth_root_cause"]
    scen3_sentinel_top = scen3_sentinel[0]["service"] if scen3_sentinel else None
    scen3_sentinel_top3 = [c["service"] for c in scen3_sentinel[:3]]

    query_text_3 = "ConnectTimeout HTTPSConnectionPool api.stripe-mock.com Read timed out"
    rag_res_3 = vector_store.search(query_text_3, top_k=3, affected_service=scen3_gt)
    top_rag_3 = rag_res_3[0] if rag_res_3 else None

    evaluation_records.append({
        "scenario_id": "payment_timeout",
        "title": SCENARIO_CATALOG["payment_timeout"]["title"],
        "ground_truth_root_cause": scen3_gt,
        "telemetry_events_ingested": len(scen3_events),
        "baseline_top_1": scen3_baseline[0] if scen3_baseline else None,
        "baseline_correct": (scen3_baseline[0] == scen3_gt) if scen3_baseline else False,
        "sentinel_top_1": scen3_sentinel_top,
        "sentinel_top_1_correct": scen3_sentinel_top == scen3_gt,
        "sentinel_top_3_correct": scen3_gt in scen3_sentinel_top3,
        "sentinel_confidence": scen3_sentinel[0]["confidence"] if scen3_sentinel else "UNKNOWN",
        "top_rag_doc_id": top_rag_3.doc_id if top_rag_3 else None,
        "top_rag_similarity": top_rag_3.similarity_score if top_rag_3 else 0.0,
        "rag_relevant_match": (top_rag_3.doc_id in (SCENARIO_CATALOG["payment_timeout"]["historical_incident_id"], SCENARIO_CATALOG["payment_timeout"].get("historical_runbook_id"))) if top_rag_3 else False,
        "supporting_evidence": scen3_sentinel[0]["reasons"] if scen3_sentinel else [],
    })

    # -------------------------------------------------------------------------
    # Scenario 4: Misleading Symptom Cascade (Stress Test for Baseline Failure)
    # -------------------------------------------------------------------------
    store.clear()
    now = time.time()
    # Upstream root trigger: 1 database deadlock on order-service
    store.add_events([
        TelemetryEvent(
            event_id="e-deadlock-root",
            timestamp=now,
            service="order-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="Deadlock detected while waiting for lock on relation orders_pkey",
            trace_id="tr-flood-0",
            span_id="sp-order-0",
            parent_span_id="sp-gw-0"
        )
    ])
    # Downstream noisy cascade: web-gateway floods 20 502/500 errors
    flood_events = [
        TelemetryEvent(
            event_id=f"e-gw-flood-{i}",
            timestamp=now + 0.02 + (i * 0.01),
            service="web-gateway",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message=f"HTTP 502 Bad Gateway while processing order item #{i}",
            trace_id=f"tr-flood-{i}",
            span_id=f"sp-gw-{i}"
        )
        for i in range(20)
    ]
    store.add_events(flood_events)
    scen4_events = store.get_events()

    scen4_baseline = baseline_error_count_ranker(scen4_events)
    scen4_sentinel, _, _ = run_sentinel_graph_ranking(scen4_events)
    scen4_gt = "order-service"
    scen4_sentinel_top = scen4_sentinel[0]["service"] if scen4_sentinel else None
    scen4_sentinel_top3 = [c["service"] for c in scen4_sentinel[:3]]

    # Noise rejection check in RAG: Unrelated query should return no high-score doc
    unrelated_query = "Stripe webhook InvalidSignatureException clock skew timestamp outside tolerance"
    rag_res_4 = vector_store.search(unrelated_query, top_k=3, affected_service="order-service")
    noise_rejected = len(rag_res_4) == 0 or all(r.similarity_score < 0.40 for r in rag_res_4)

    evaluation_records.append({
        "scenario_id": "misleading_gateway_flood",
        "title": "Downstream Symptom Flood vs Single Upstream Trigger",
        "ground_truth_root_cause": scen4_gt,
        "telemetry_events_ingested": len(scen4_events),
        "baseline_top_1": scen4_baseline[0] if scen4_baseline else None,
        "baseline_correct": (scen4_baseline[0] == scen4_gt) if scen4_baseline else False,
        "sentinel_top_1": scen4_sentinel_top,
        "sentinel_top_1_correct": scen4_sentinel_top == scen4_gt,
        "sentinel_top_3_correct": scen4_gt in scen4_sentinel_top3,
        "sentinel_confidence": scen4_sentinel[0]["confidence"] if scen4_sentinel else "UNKNOWN",
        "top_rag_doc_id": rag_res_4[0].doc_id if rag_res_4 else None,
        "top_rag_similarity": rag_res_4[0].similarity_score if rag_res_4 else 0.0,
        "rag_relevant_match": False,  # Ground truth is unindexed / noise
        "noise_properly_rejected": noise_rejected,
        "supporting_evidence": scen4_sentinel[0]["reasons"] if scen4_sentinel else [],
    })

    # -------------------------------------------------------------------------
    # Compute Aggregate Benchmark Metrics
    # -------------------------------------------------------------------------
    total_scenarios = len(evaluation_records)
    baseline_top1_correct = sum(1 for r in evaluation_records if r["baseline_correct"])
    sentinel_top1_correct = sum(1 for r in evaluation_records if r["sentinel_top_1_correct"])
    sentinel_top3_correct = sum(1 for r in evaluation_records if r["sentinel_top_3_correct"])
    rag_matches_correct = sum(1 for r in evaluation_records[:3] if r["rag_relevant_match"])

    baseline_top1_acc = round(baseline_top1_correct / total_scenarios, 4)
    sentinel_top1_acc = round(sentinel_top1_correct / total_scenarios, 4)
    sentinel_top3_acc = round(sentinel_top3_correct / total_scenarios, 4)
    rag_hit1_acc = round(rag_matches_correct / 3, 4)

    results_data = {
        "evaluation_name": "SENTINEL Phase 8 Real-World Incident Evaluation",
        "timestamp": time.time(),
        "total_scenarios_evaluated": total_scenarios,
        "summary_metrics": {
            "baseline_error_count_top1_accuracy": baseline_top1_acc,
            "sentinel_causal_graph_top1_accuracy": sentinel_top1_acc,
            "sentinel_causal_graph_top3_accuracy": sentinel_top3_acc,
            "historical_rag_hit1_accuracy": rag_hit1_acc,
            "rag_noise_rejection_verified": noise_rejected,
        },
        "detailed_scenarios": evaluation_records
    }

    # Save machine-readable evaluation results
    output_path = os.path.join(os.path.dirname(__file__), "..", "evaluation_results_phase8.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print("\n=================================================================")
    print("PHASE 8 REAL-WORLD INCIDENT EVALUATION RESULTS")
    print(f"Total Scenarios Evaluated: {total_scenarios}")
    print(f"Baseline Error Count Top-1 Accuracy: {baseline_top1_acc:.1%} ({baseline_top1_correct}/{total_scenarios})")
    print(f"SENTINEL Causal Graph Top-1 Accuracy: {sentinel_top1_acc:.1%} ({sentinel_top1_correct}/{total_scenarios})")
    print(f"SENTINEL Causal Graph Top-3 Accuracy: {sentinel_top3_acc:.1%} ({sentinel_top3_correct}/{total_scenarios})")
    print(f"Historical RAG Hit@1 Accuracy:        {rag_hit1_acc:.1%} ({rag_matches_correct}/3)")
    print(f"Noise Rejection Filter:               {'PASSED' if noise_rejected else 'FAILED'}")
    print(f"Machine-Readable Results Written To:  {os.path.abspath(output_path)}")
    print("=================================================================\n")

    # Assertions
    assert sentinel_top1_acc == 1.0, f"Expected 100% Top-1 accuracy, got {sentinel_top1_acc:.1%}"
    assert sentinel_top3_acc == 1.0, f"Expected 100% Top-3 accuracy, got {sentinel_top3_acc:.1%}"
    assert sentinel_top1_acc > baseline_top1_acc, "SENTINEL graph ranker must outperform baseline error counting"
    assert rag_hit1_acc == 1.0, "Historical RAG must accurately retrieve indexed precedents"
    assert noise_rejected is True, "RAG noise rejection filter must reject unindexed queries"

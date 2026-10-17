"""Phase 9 Comprehensive Evaluation Test Suite.
Tasks 3 & 4:
- Evaluates 8 failure scenarios (4 dev fixtures + 4 held-out evaluation cases).
- Tests Baseline Error Counting vs SENTINEL Causal Graph Ranking.
- Evaluates Top-1 & Top-3 accuracy, reporting denominator and individual failures.
- Verifies that inconclusive/insufficient evidence produces LOW confidence / uncertainty disclosures.
- Evaluates Graph-Only vs Graph-plus-Historical RAG separately.
- Verifies RAG noise rejection and distractor incident separation.
- Exports machine-readable results to backend/evaluation_results_phase9.json.
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
from demo_app.scenarios_phase9 import (
    PHASE9_EVALUATION_DATASET,
    generate_scenario_telemetry,
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
def setup_evaluation_environment():
    """Ensure clean store and freshly indexed knowledge base before tests."""
    store.clear()
    initialize_knowledge_base()
    yield
    store.clear()


def test_phase9_expanded_evaluation():
    """Run evaluation across all 8 scenarios, comparing baseline, graph-only, and graph-plus-RAG."""
    evaluation_records: List[Dict[str, Any]] = []

    for scenario_id, meta in PHASE9_EVALUATION_DATASET.items():
        events = generate_scenario_telemetry(scenario_id)
        gt_cause = meta["ground_truth_root_cause"]
        is_inconclusive = meta["is_inconclusive"]

        # 1. Baseline Ranking
        baseline_ranked = baseline_error_count_ranker(events)
        baseline_top1 = baseline_ranked[0] if baseline_ranked else None

        # 2. SENTINEL Graph Ranking (Without RAG)
        sentinel_candidates, nodes, raw_causes = run_sentinel_graph_ranking(events)
        sentinel_top1 = sentinel_candidates[0]["service"] if sentinel_candidates else None
        sentinel_top3 = [c["service"] for c in sentinel_candidates[:3]]
        sentinel_confidence = sentinel_candidates[0]["confidence"] if sentinel_candidates else "LOW"

        # Check accuracy for deterministic cases
        if not is_inconclusive:
            baseline_correct = (baseline_top1 == gt_cause)
            sentinel_top1_correct = (sentinel_top1 == gt_cause)
            sentinel_top3_correct = (gt_cause in sentinel_top3)
        else:
            # Inconclusive case: true cause is absent/ambiguous; ranker must NOT claim high confidence
            baseline_correct = False
            sentinel_top1_correct = None
            sentinel_top3_correct = None

        # 3. Historical RAG Retrieval
        rag_query = f"{meta['title']} {sentinel_top1 or ''}"
        rag_results = vector_store.search(rag_query, top_k=3, affected_service=sentinel_top1)
        top_rag = rag_results[0] if rag_results else None

        # Check RAG match if expected
        expected_docs = [d for d in (meta.get("historical_incident_id"), meta.get("historical_runbook_id")) if d]
        if expected_docs:
            rag_match_correct = (top_rag.doc_id in expected_docs) if top_rag else False
        else:
            # No historical document exists for this scenario
            rag_match_correct = None

        # 4. Graph + Historical RAG Synthesis
        synthesis = synthesize_investigation(
            nodes=nodes,
            ranked_causes=raw_causes,
            top_k=3,
        )

        # Verify strict separation in synthesis
        assert len(synthesis.observed_facts) > 0, "Observed facts must be present"
        assert len(synthesis.root_cause_hypotheses) > 0, "Hypotheses must be present"
        assert len(synthesis.uncertainty_disclosures) > 0, "Uncertainty disclosures must be present"

        # Verify non-causal disclaimer in uncertainty disclosures
        has_non_causal_disclaimer = any(
            "historical" in u.lower() or "not direct" in u.lower() or "precedent" in u.lower()
            for u in synthesis.uncertainty_disclosures
        )
        assert has_non_causal_disclaimer, "Synthesis must explicitly disclose that historical records do not prove current cause"

        record = {
            "scenario_id": scenario_id,
            "title": meta["title"],
            "held_out": meta["held_out"],
            "is_inconclusive": is_inconclusive,
            "ground_truth_root_cause": gt_cause,
            "telemetry_events_ingested": len(events),
            "baseline_top_1": baseline_top1,
            "baseline_correct": baseline_correct,
            "sentinel_top_1": sentinel_top1,
            "sentinel_top_1_correct": sentinel_top1_correct,
            "sentinel_top_3_correct": sentinel_top3_correct,
            "sentinel_confidence": sentinel_confidence,
            "top_rag_doc_id": top_rag.doc_id if top_rag else None,
            "top_rag_similarity": top_rag.similarity_score if top_rag else 0.0,
            "rag_relevant_match": rag_match_correct,
            "supporting_evidence": sentinel_candidates[0]["reasons"] if sentinel_candidates else [],
            "uncertainty_disclosures": synthesis.uncertainty_disclosures,
        }
        evaluation_records.append(record)

    # -------------------------------------------------------------------------
    # Evaluation Calculations
    # -------------------------------------------------------------------------
    deterministic_records = [r for r in evaluation_records if not r["is_inconclusive"]]
    n_det = len(deterministic_records)

    baseline_top1_hits = sum(1 for r in deterministic_records if r["baseline_correct"])
    sentinel_top1_hits = sum(1 for r in deterministic_records if r["sentinel_top_1_correct"])
    sentinel_top3_hits = sum(1 for r in deterministic_records if r["sentinel_top_3_correct"])

    baseline_top1_acc = round(baseline_top1_hits / n_det, 4)
    sentinel_top1_acc = round(sentinel_top1_hits / n_det, 4)
    sentinel_top3_acc = round(sentinel_top3_hits / n_det, 4)

    # Held-out subset evaluation
    held_out_det = [r for r in deterministic_records if r["held_out"]]
    held_out_baseline_hits = sum(1 for r in held_out_det if r["baseline_correct"])
    held_out_sentinel_hits = sum(1 for r in held_out_det if r["sentinel_top_1_correct"])

    # Inconclusive scenario handling verification
    inconclusive_rec = next(r for r in evaluation_records if r["is_inconclusive"])
    # Sentinel must not claim HIGH confidence on disconnected/insufficient evidence
    inconclusive_handled_honestly = inconclusive_rec["sentinel_confidence"] in ("LOW", "MEDIUM")

    # Historical RAG metrics
    rag_eval_records = [r for r in evaluation_records if r["rag_relevant_match"] is not None]
    rag_hits = sum(1 for r in rag_eval_records if r["rag_relevant_match"] is True)
    rag_hit1_acc = round(rag_hits / len(rag_eval_records), 4) if rag_eval_records else 0.0

    # Distractor check: Query unrelated DDoS incident against database failure
    db_query = "PostgreSQL deadlock lock relation orders_pkey"
    distractor_search = vector_store.search(db_query, top_k=3, affected_service="order-service")
    distractor_rejected = not any(res.doc_id == "INC-2024-0410" for res in distractor_search)

    # Compile machine-readable results
    results_payload = {
        "evaluation_name": "SENTINEL Phase 9 Independent & Distributed Evaluation",
        "timestamp": time.time(),
        "total_scenarios": len(evaluation_records),
        "deterministic_scenarios_count": n_det,
        "held_out_scenarios_count": len(held_out_det),
        "summary_metrics": {
            "baseline_top1_accuracy": f"{baseline_top1_acc:.1%} ({baseline_top1_hits}/{n_det})",
            "sentinel_top1_accuracy": f"{sentinel_top1_acc:.1%} ({sentinel_top1_hits}/{n_det})",
            "sentinel_top3_accuracy": f"{sentinel_top3_acc:.1%} ({sentinel_top3_hits}/{n_det})",
            "held_out_sentinel_top1_accuracy": f"{(held_out_sentinel_hits / len(held_out_det)):.1%} ({held_out_sentinel_hits}/{len(held_out_det)})",
            "held_out_baseline_top1_accuracy": f"{(held_out_baseline_hits / len(held_out_det)):.1%} ({held_out_baseline_hits}/{len(held_out_det)})",
            "inconclusive_scenario_handled_honestly": inconclusive_handled_honestly,
            "historical_rag_hit1_accuracy": f"{rag_hit1_acc:.1%} ({rag_hits}/{len(rag_eval_records)})",
            "distractor_ddos_noise_rejected": distractor_rejected,
        },
        "detailed_scenarios": evaluation_records,
    }

    results_path = os.path.join(os.path.dirname(__file__), "..", "evaluation_results_phase9.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print("\n=================================================================")
    print("PHASE 9 INDEPENDENT & DISTRIBUTED EVALUATION RESULTS")
    print(f"Total Scenarios Evaluated:                {len(evaluation_records)} (7 Deterministic + 1 Inconclusive)")
    print(f"Baseline Error Count Top-1 Accuracy:      {baseline_top1_acc:.1%} ({baseline_top1_hits}/{n_det})")
    print(f"SENTINEL Causal Graph Top-1 Accuracy:     {sentinel_top1_acc:.1%} ({sentinel_top1_hits}/{n_det})")
    print(f"SENTINEL Causal Graph Top-3 Accuracy:     {sentinel_top3_acc:.1%} ({sentinel_top3_hits}/{n_det})")
    print(f"Held-Out Generalization Top-1 Accuracy:   {(held_out_sentinel_hits / len(held_out_det)):.1%} vs Baseline {(held_out_baseline_hits / len(held_out_det)):.1%}")
    print(f"Inconclusive Case Handled Honestly:       {'YES (LOW/MEDIUM confidence flagged)' if inconclusive_handled_honestly else 'NO'}")
    print(f"Historical RAG Hit@1 Accuracy:            {rag_hit1_acc:.1%} ({rag_hits}/{len(rag_eval_records)})")
    print(f"Distractor DDoS Noise Rejected:           {'PASSED' if distractor_rejected else 'FAILED'}")
    print(f"Machine-Readable Results Saved To:        {os.path.abspath(results_path)}")
    print("=================================================================\n")

    # Assertions
    assert sentinel_top1_acc == 1.0, f"Expected 100% Top-1 accuracy on deterministic cases, got {sentinel_top1_acc:.1%}"
    assert sentinel_top1_acc > baseline_top1_acc, "SENTINEL graph ranking must outperform raw error counting"
    assert inconclusive_handled_honestly is True, "Inconclusive scenario must not claim high confidence"
    assert distractor_rejected is True, "Distractor incident must be rejected on database query"

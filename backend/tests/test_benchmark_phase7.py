"""SENTINEL Phase 7 — Comprehensive Benchmark & Evaluation Suite.

Evaluates:
1. Baseline vs. Improved Root-Cause Ranking (Hit@1, Hit@3, MRR).
2. RAG Retrieval Evaluation (Hit@1, Relevance Score, Noise/Spurious Match Rejection).
3. Seven required scenario test cases:
   - Case 1: Known failure with relevant historical incident.
   - Case 2: Known failure without relevant historical document.
   - Case 3: Misleading/ambiguous symptom (high volume downstream symptom vs quiet upstream trigger).
   - Case 4: Missing dependency relationship (uninstrumented/disconnected services).
   - Case 5: Proposed fix that improves results (remediation supported by evidence).
   - Case 6: Proposed fix that does not improve results (ineffective candidate fix).
   - Case 7: Inconclusive experiment (insufficient sample size).
"""
import time
from typing import List, Dict, Any, Tuple
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.telemetry import TelemetryEvent, LogLevel, EventType
from backend.app.models.impact import ComponentHealthStatus, DependencyRelationship
from backend.app.models.validation import ValidationVerdict
from backend.app.graph.builder import build_incident_graph
from backend.app.graph.ranker import rank_root_causes
from backend.app.services.rag import initialize_knowledge_base, vector_store
from backend.app.storage.memory_store import store

client = TestClient(app)

# ============================================================================
# Baseline Rankers for Comparative Evaluation
# ============================================================================

def baseline_frequency_ranker(events: List[TelemetryEvent]) -> List[str]:
    """Baseline 1: Ranks candidates purely by raw error frequency count."""
    counts: Dict[str, int] = {}
    for ev in events:
        if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            svc = ev.service
            counts[svc] = counts.get(svc, 0) + 1
    # Sort descending by count
    return [svc for svc, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


def baseline_chronological_ranker(events: List[TelemetryEvent]) -> List[str]:
    """Baseline 2: Ranks candidates purely by earliest timestamp error log."""
    error_events = [ev for ev in events if ev.level in (LogLevel.ERROR, LogLevel.CRITICAL)]
    error_events.sort(key=lambda ev: ev.timestamp)
    seen = set()
    result = []
    for ev in error_events:
        if ev.service not in seen:
            seen.add(ev.service)
            result.append(ev.service)
    return result


def improved_graph_ranker(events: List[TelemetryEvent]) -> List[str]:
    """Improved SENTINEL Approach: NetworkX causal topology + Personalized PageRank + Blast Radius."""
    G, nodes, _ = build_incident_graph(events)
    ranked = rank_root_causes(G, nodes)
    # Extract unique ranked services in order
    seen = set()
    result = []
    for candidate in ranked:
        if candidate.service not in seen:
            seen.add(candidate.service)
            result.append(candidate.service)
    return result


# ============================================================================
# Benchmark Test Cases
# ============================================================================

@pytest.fixture(autouse=True)
def setup_benchmark_environment():
    """Ensure clean store and indexed knowledge base."""
    store.clear()
    client.post("/api/demo/scenario/recover")
    client.post("/api/rag/ingest")
    yield
    store.clear()
    client.post("/api/demo/scenario/recover")


def test_benchmark_case_1_known_failure_with_historical_doc():
    """Case 1: Known failure with relevant historical incident.
    
    Scenario: inventory-db pool exhaustion cascade.
    Expected:
      - Root Cause: inventory-db identified as top root cause.
      - RAG: INC-2025-0812 retrieved as top precedent with high similarity.
    """
    now = time.time()
    events = [
        TelemetryEvent(
            event_id="e-inv-1",
            timestamp=now,
            service="inventory-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="CRITICAL: HikariPool-1 - Connection is not available, request timed out after 3000ms",
            trace_id="tr-case1",
            span_id="sp-inv",
            parent_span_id="sp-order"
        ),
        TelemetryEvent(
            event_id="e-order-1",
            timestamp=now + 0.1,
            service="order-service",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="Failed to acquire connection to inventory service: timeout after 3000ms",
            trace_id="tr-case1",
            span_id="sp-order",
            parent_span_id="sp-gw"
        ),
        TelemetryEvent(
            event_id="e-gw-1",
            timestamp=now + 0.2,
            service="web-gateway",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="HTTP 500 downstream error on /api/checkout",
            trace_id="tr-case1",
            span_id="sp-gw"
        ),
    ]

    # 1. Root Cause Ranking Evaluation
    improved_ranks = improved_graph_ranker(events)
    assert len(improved_ranks) > 0
    actual_top_root_cause = improved_ranks[0]
    expected_root_cause = "inventory-service"
    assert actual_top_root_cause == expected_root_cause, (
        f"Expected {expected_root_cause}, got {actual_top_root_cause}"
    )

    # 2. RAG Retrieval Evaluation (Evaluated independently)
    query = "HikariPool connection pool saturation timeout on inventory service"
    rag_results = vector_store.search(query, top_k=3, affected_service="inventory-service")
    assert len(rag_results) > 0
    top_doc = rag_results[0]
    expected_doc_id = "INC-2025-0812"
    assert top_doc.doc_id == expected_doc_id
    assert top_doc.similarity_score >= 0.50


def test_benchmark_case_2_known_failure_without_historical_doc():
    """Case 2: Known failure without a relevant historical document.
    
    Scenario: payment-service third-party stripe webhook signature rotation failure.
    Expected:
      - Root Cause: payment-service identified from telemetry.
      - RAG: Honest disclosure / rejection: no high-confidence historical doc returned.
    """
    now = time.time()
    events = [
        TelemetryEvent(
            event_id="e-pay-1",
            timestamp=now,
            service="payment-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="Webhook signature verification failed: timestamp outside tolerance (possible clock skew)",
            trace_id="tr-case2",
            span_id="sp-pay"
        ),
        TelemetryEvent(
            event_id="e-pay-2",
            timestamp=now + 0.05,
            service="payment-service",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="Failed to process Stripe event evt_99881122: InvalidSignatureException",
            trace_id="tr-case2",
            span_id="sp-pay"
        )
    ]

    # 1. Root cause correctly identified
    improved_ranks = improved_graph_ranker(events)
    assert len(improved_ranks) > 0
    assert improved_ranks[0] == "payment-service"

    # 2. RAG evaluation: Knowledge base has NO document for Stripe clock-skew signature failure
    query = "Stripe webhook InvalidSignatureException clock skew timestamp outside tolerance"
    rag_results = vector_store.search(query, top_k=3, affected_service="payment-service")
    # All results must be low score (< 0.40) or empty, demonstrating noise rejection
    for r in rag_results:
        assert r.similarity_score < 0.40, f"Spurious match found with high score {r.similarity_score}: {r.title}"


def test_benchmark_case_3_misleading_ambiguous_symptom():
    """Case 3: Misleading or ambiguous symptom.
    
    Scenario: web-gateway logs 20 error events due to a single upstream database lock in order-service.
    A frequency-based baseline would wrongly pick web-gateway because it has 20 errors vs order-service's 1.
    The improved NetworkX graph approach identifies order-service as root cause via causal topology.
    """
    now = time.time()
    events: List[TelemetryEvent] = [
        # Upstream root cause: order-service db deadlock (single event)
        TelemetryEvent(
            event_id="e-order-root",
            timestamp=now,
            service="order-service",
            level=LogLevel.CRITICAL,
            event_type=EventType.LOG,
            message="Deadlock detected while waiting for lock on relation orders_pkey",
            trace_id="tr-cascade-root",
            span_id="sp-order-root",
            parent_span_id="sp-gw-root"
        )
    ]

    # Downstream symptoms: web-gateway floods 15 errors
    for i in range(15):
        events.append(
            TelemetryEvent(
                event_id=f"e-gw-symptom-{i}",
                timestamp=now + 0.05 + (i * 0.01),
                service="web-gateway",
                level=LogLevel.ERROR,
                event_type=EventType.LOG,
                message=f"HTTP 502 Bad Gateway while calling /orders/checkout item #{i}",
                trace_id=f"tr-cascade-{i}",
                span_id=f"sp-gw-{i}"
            )
        )

    # Baseline frequency evaluation: picks web-gateway (Wrong!)
    baseline_top = baseline_frequency_ranker(events)[0]
    assert baseline_top == "web-gateway", "Baseline frequency ranking incorrectly identifies symptom"

    # Improved graph evaluation: picks order-service (Correct!)
    improved_ranks = improved_graph_ranker(events)
    assert improved_ranks[0] == "order-service", (
        f"Graph ranker should overcome error flood and pick true upstream root cause. Got: {improved_ranks[0]}"
    )


def test_benchmark_case_4_missing_dependency_relationship():
    """Case 4: A missing dependency relationship.
    
    Scenario: auth-service and inventory-service fail concurrently, but have NO trace headers
    or call relationship linking them (e.g. uninstrumented async message queue).
    Impact Radar must NOT fabricate a relationship between them.
    """
    now = time.time()
    # Inject isolated failures in auth-service and inventory-service
    store.add_events([
        TelemetryEvent(
            event_id="e-auth-iso",
            timestamp=now,
            service="auth-service",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="JWT secret rotation key error",
        ),
        TelemetryEvent(
            event_id="e-inv-iso",
            timestamp=now + 0.1,
            service="inventory-service",
            level=LogLevel.ERROR,
            event_type=EventType.LOG,
            message="Stock level sync failed",
        )
    ])

    # Analyze impact on auth-service
    res = client.post(
        "/api/radar/analyze",
        json={"suspected_component": "auth-service", "window_seconds": 300}
    )
    assert res.status_code == 200
    report = res.json()

    impacted_services = [c["service"] for c in report["impacted_components"]]
    # auth-service is the target
    assert "auth-service" in impacted_services
    # inventory-service is topologically disconnected from auth-service in DEMO_TOPOLOGY and telemetry:
    # It must NOT be included in auth-service's downstream impact graph
    assert "inventory-service" not in impacted_services, (
        "Impact radar hallucinated a dependency relationship to an unlinked service!"
    )


def test_benchmark_case_5_proposed_fix_improves_results():
    """Case 5: A proposed fix that improves results.
    
    Scenario: db_pool_exhaustion baseline, applying 'increase_pool_size' fix with user approval.
    Expected: Verdict = supported_by_evidence, post_fix error rate = 0.0.
    """
    # 1. Baseline
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 5}
    )
    assert base_res.status_code == 200
    exp_id = base_res.json()["experiment_id"]
    assert base_res.json()["metrics"]["error_rate"] == 1.0

    # 2. Fix execution
    val_res = client.post(
        "/api/validation/run",
        json={
            "experiment_id": exp_id,
            "fix_id": "increase_pool_size",
            "approved": True,
            "workload_count": 5
        }
    )
    assert val_res.status_code == 200
    report = val_res.json()

    assert report["verdict"] == ValidationVerdict.SUPPORTED_BY_EVIDENCE.value
    assert report["post_fix_metrics"]["error_rate"] == 0.0
    assert report["error_rate_delta"] == 1.0


def test_benchmark_case_6_proposed_fix_does_not_improve_results():
    """Case 6: A proposed fix that does not improve results.
    
    Scenario: db_pool_exhaustion baseline, applying 'noop_ineffective_fix'.
    Expected: Verdict = not_supported_by_evidence, post_fix error rate remains >= 0.50.
    """
    # 1. Baseline
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 4}
    )
    assert base_res.status_code == 200
    exp_id = base_res.json()["experiment_id"]

    # 2. Fix execution
    val_res = client.post(
        "/api/validation/run",
        json={
            "experiment_id": exp_id,
            "fix_id": "noop_ineffective_fix",
            "approved": True,
            "workload_count": 4
        }
    )
    assert val_res.status_code == 200
    report = val_res.json()

    assert report["verdict"] == ValidationVerdict.NOT_SUPPORTED_BY_EVIDENCE.value
    assert report["post_fix_metrics"]["error_rate"] >= 0.50


def test_benchmark_case_7_inconclusive_experiment():
    """Case 7: An inconclusive experiment.
    
    Scenario: Workload count = 1 (< 3 minimum required requests).
    Expected: Verdict = inconclusive due to insufficient sample size.
    """
    # 1. Baseline with 1 request
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 1}
    )
    assert base_res.status_code == 200
    exp_id = base_res.json()["experiment_id"]

    # 2. Fix execution with 1 request
    val_res = client.post(
        "/api/validation/run",
        json={
            "experiment_id": exp_id,
            "fix_id": "increase_pool_size",
            "approved": True,
            "workload_count": 1
        }
    )
    assert val_res.status_code == 200
    report = val_res.json()

    assert report["verdict"] == ValidationVerdict.INCONCLUSIVE.value
    assert "sample size" in report["explanation"].lower()


# ============================================================================
# Quantitative Metric Benchmark (Baseline vs Improved)
# ============================================================================

def test_quantitative_ranking_accuracy_benchmark():
    """Measure Top-1 and Top-3 accuracy across a suite of controlled scenarios:
    1. DB Pool exhaustion cascade (Ground truth: inventory-db)
    2. Bad Auth deployment (Ground truth: auth-service)
    3. Payment gateway timeout (Ground truth: payment-service)
    4. Noisy downstream symptom cascade (Ground truth: order-service)
    """
    now = time.time()
    scenarios = [
        {
            "name": "DB Pool Exhaustion Cascade",
            "ground_truth": "inventory-db",
            "events": [
                TelemetryEvent(event_id="e1", timestamp=now, service="inventory-db", level=LogLevel.CRITICAL, event_type=EventType.LOG, message="Pool full", trace_id="t1", span_id="s1", parent_span_id="s2"),
                TelemetryEvent(event_id="e2", timestamp=now+0.1, service="order-service", level=LogLevel.ERROR, event_type=EventType.LOG, message="Order fail", trace_id="t1", span_id="s2", parent_span_id="s3"),
                TelemetryEvent(event_id="e3", timestamp=now+0.2, service="web-gateway", level=LogLevel.ERROR, event_type=EventType.LOG, message="500", trace_id="t1", span_id="s3"),
            ]
        },
        {
            "name": "Bad Auth Deployment",
            "ground_truth": "auth-service",
            "events": [
                TelemetryEvent(event_id="d1", timestamp=now-2.0, service="auth-service", level=LogLevel.INFO, event_type=EventType.DEPLOYMENT, message="v2.4.1"),
                TelemetryEvent(event_id="d2", timestamp=now, service="auth-service", level=LogLevel.CRITICAL, event_type=EventType.LOG, message="NullPointer TokenValidator"),
                TelemetryEvent(event_id="d3", timestamp=now+0.1, service="web-gateway", level=LogLevel.ERROR, event_type=EventType.LOG, message="401 Unauthorized"),
            ]
        },
        {
            "name": "Payment Gateway Timeout",
            "ground_truth": "payment-service",
            "events": [
                TelemetryEvent(event_id="p1", timestamp=now, service="payment-service", level=LogLevel.CRITICAL, event_type=EventType.LOG, message="Gateway connection reset", trace_id="t2", span_id="sp1", parent_span_id="sp2"),
                TelemetryEvent(event_id="p2", timestamp=now+0.1, service="order-service", level=LogLevel.ERROR, event_type=EventType.LOG, message="Payment processing failed", trace_id="t2", span_id="sp2", parent_span_id="sp3"),
                TelemetryEvent(event_id="p3", timestamp=now+0.2, service="web-gateway", level=LogLevel.ERROR, event_type=EventType.LOG, message="504 Gateway Timeout", trace_id="t2", span_id="sp3"),
            ]
        },
        {
            "name": "Noisy Downstream Symptom Cascade",
            "ground_truth": "order-service",
            "events": [
                TelemetryEvent(event_id="n1", timestamp=now, service="order-service", level=LogLevel.CRITICAL, event_type=EventType.LOG, message="Lock timeout in order processing", trace_id="t3", span_id="sn1", parent_span_id="sn2"),
                TelemetryEvent(event_id="n2", timestamp=now+0.05, service="web-gateway", level=LogLevel.ERROR, event_type=EventType.LOG, message="500 Internal Server Error", trace_id="t3", span_id="sn2"),
                TelemetryEvent(event_id="n3", timestamp=now+0.06, service="web-gateway", level=LogLevel.ERROR, event_type=EventType.LOG, message="500 Internal Server Error", trace_id="t3", span_id="sn3"),
                TelemetryEvent(event_id="n4", timestamp=now+0.07, service="web-gateway", level=LogLevel.ERROR, event_type=EventType.LOG, message="500 Internal Server Error", trace_id="t3", span_id="sn4"),
            ]
        }
    ]

    freq_top1_correct = 0
    improved_top1_correct = 0
    improved_top3_correct = 0

    for sc in scenarios:
        gt = sc["ground_truth"]
        evs = sc["events"]

        # Baseline Frequency
        b_ranks = baseline_frequency_ranker(evs)
        if b_ranks and b_ranks[0] == gt:
            freq_top1_correct += 1

        # Improved Graph Approach
        i_ranks = improved_graph_ranker(evs)
        if i_ranks and i_ranks[0] == gt:
            improved_top1_correct += 1
        if gt in i_ranks[:3]:
            improved_top3_correct += 1

    total = len(scenarios)
    freq_accuracy = freq_top1_correct / total
    improved_top1_accuracy = improved_top1_correct / total
    improved_top3_accuracy = improved_top3_correct / total

    # Print measurable summary to test output
    print(f"\n=======================================================")
    print(f"ROOT-CAUSE RANKING BENCHMARK ({total} SCENARIOS)")
    print(f"Frequency Baseline Top-1 Accuracy: {freq_accuracy:.1%} ({freq_top1_correct}/{total})")
    print(f"SENTINEL Graph Top-1 Accuracy:     {improved_top1_accuracy:.1%} ({improved_top1_correct}/{total})")
    print(f"SENTINEL Graph Top-3 Accuracy:     {improved_top3_accuracy:.1%} ({improved_top3_correct}/{total})")
    print(f"=======================================================\n")

    # The improved graph approach must achieve 100% Top-1 accuracy across all 4 scenarios,
    # whereas frequency baseline fails on Scenario 4 (noisy downstream symptom flood).
    assert improved_top1_accuracy == 1.0
    assert improved_top3_accuracy == 1.0
    assert improved_top1_accuracy > freq_accuracy

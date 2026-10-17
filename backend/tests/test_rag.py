"""Evaluation benchmark and tests for Phase 6: RAG-Powered Historical Incident Intelligence."""
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.rag import (
    initialize_knowledge_base,
    load_knowledge_directory,
    vector_store,
)
from backend.app.storage.memory_store import store

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_indexed():
    """Ensure knowledge base is indexed for each test."""
    store.clear()
    initialize_knowledge_base()
    yield
    store.clear()

def test_rag_ingestion_pipeline():
    """Verify discovery, metadata extraction, and chunk indexing."""
    res = client.post("/api/rag/ingest")
    assert res.status_code == 200
    data = res.json()

    assert data["documents_discovered"] >= 5
    assert data["chunks_indexed"] >= 5
    assert data["total_tokens"] > 100
    assert any("INC-2025-0812" in s for s in data["sources"])

    # Document list endpoint
    doc_res = client.get("/api/rag/documents")
    assert doc_res.status_code == 200
    docs = doc_res.json()
    assert len(docs) >= 5
    doc_ids = [d["doc_id"] for d in docs]
    assert "INC-2025-0812" in doc_ids
    assert "INC-2025-1104" in doc_ids
    assert "INC-2026-0115" in doc_ids
    assert "RUNBOOK-INV-001" in doc_ids
    assert "RUNBOOK-AUTH-002" in doc_ids

def test_rag_retrieval_benchmark_hit_at_k():
    """Benchmark retrieval accuracy and compute Hit@1 and Hit@3 across known failure queries."""
    benchmark_cases = [
        {
            "query": "HikariPool connection pool saturation timeout on inventory service",
            "service": "inventory-service",
            "expected_doc_ids": ["INC-2025-0812", "RUNBOOK-INV-001"],
        },
        {
            "query": "NullPointerDereference in TokenValidator.verify session token is None",
            "service": "auth-service",
            "expected_doc_ids": ["INC-2025-1104", "RUNBOOK-AUTH-002"],
        },
        {
            "query": "ConnectTimeout HTTPSConnectionPool api.stripe-mock.com 504 gateway timeout",
            "service": "payment-service",
            "expected_doc_ids": ["INC-2026-0115"],
        },
    ]

    hit_at_1_count = 0
    hit_at_3_count = 0

    for case in benchmark_cases:
        res = client.post(
            "/api/rag/query",
            json={
                "query_text": case["query"],
                "affected_service": case["service"],
                "top_k": 3,
            }
        )
        assert res.status_code == 200
        retrieved = res.json()
        assert len(retrieved) > 0

        retrieved_doc_ids = [r["doc_id"] for r in retrieved]
        top_1_doc = retrieved[0]["doc_id"]

        # Hit@1
        if top_1_doc in case["expected_doc_ids"]:
            hit_at_1_count += 1

        # Hit@3
        if any(doc in case["expected_doc_ids"] for doc in retrieved_doc_ids[:3]):
            hit_at_3_count += 1

        # Verify similarity score quality
        assert retrieved[0]["similarity_score"] >= 0.35
        assert len(retrieved[0]["excerpt"]) > 20
        assert retrieved[0]["relevance_reason"] is not None

    hit_at_1_rate = hit_at_1_count / len(benchmark_cases)
    hit_at_3_rate = hit_at_3_count / len(benchmark_cases)

    # 100% Hit@1 and Hit@3 expected on curated benchmarks
    assert hit_at_1_rate == 1.0
    assert hit_at_3_rate == 1.0

def test_rag_retrieval_unrelated_query_empty_or_low_score():
    """Verify behavior when no relevant knowledge source exists."""
    res = client.post(
        "/api/rag/query",
        json={
            "query_text": "Quantum satellite teleportation cryogenic coolant leak",
            "affected_service": "orbital-relay",
            "top_k": 3,
        }
    )
    assert res.status_code == 200
    retrieved = res.json()
    # Unrelated query should return empty or low similarity noise filtered out
    assert len(retrieved) == 0

def test_incident_analysis_rag_synthesis_integration():
    """Verify end-to-end incident investigation combines facts, hypotheses, historical evidence, and uncertainty."""
    # 1. Inject failure: db_pool_exhaustion
    client.post("/api/demo/scenario/db_pool_exhaustion?count=3")

    # 2. Trigger incident analysis
    res = client.post(
        "/api/incidents/analyze",
        json={"window_seconds": 300, "title": "DB Exhaustion Live Incident"}
    )
    assert res.status_code == 200
    report = res.json()

    assert report["incident_id"] is not None
    assert report["historical_intelligence"] is not None
    intel = report["historical_intelligence"]

    # 1. Observed facts separated
    assert len(intel["observed_facts"]) >= 2
    assert any("inventory-service" in f for f in intel["observed_facts"])

    # 2. Root-cause hypotheses separated
    assert len(intel["root_cause_hypotheses"]) >= 1
    assert any("Hypothesis 1" in h for h in intel["root_cause_hypotheses"])

    # 3. Historical evidence separated
    assert len(intel["historical_evidence"]) >= 1
    top_evidence = intel["historical_evidence"][0]
    assert top_evidence["doc_id"] in ["INC-2025-0812", "RUNBOOK-INV-001"]
    assert top_evidence["similarity_score"] >= 0.40

    # 4. Recommended investigation actions derived from runbooks
    assert len(intel["recommended_investigation"]) >= 1
    assert any("Hikari" in a or "pool" in a.lower() for a in intel["recommended_investigation"])

    # 5. Uncertainty disclosures
    assert len(intel["uncertainty_disclosures"]) >= 1
    assert any("not prove causation" in u.lower() for u in intel["uncertainty_disclosures"])

    # 6. Mode verification
    assert intel["synthesizer_mode"] in ["deterministic_local", "llm_augmented"]

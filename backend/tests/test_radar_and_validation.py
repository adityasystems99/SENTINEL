"""Unit and integration tests for Phase 5: Dependency/Impact Radar & Controlled Fix Validation."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.impact import ComponentHealthStatus, DependencyRelationship
from backend.app.models.validation import ValidationVerdict
from backend.app.storage.memory_store import store

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_telemetry_store():
    """Ensure telemetry store is reset before and after each test."""
    store.clear()
    client.post("/api/demo/scenario/recover")
    yield
    store.clear()
    client.post("/api/demo/scenario/recover")

# ==========================================
# Feature 4: Impact Radar Tests
# ==========================================

def test_radar_topology_endpoint():
    """Verify service topology contains known microservices and explicit call edges."""
    res = client.get("/api/radar/topology")
    assert res.status_code == 200
    data = res.json()

    assert "nodes" in data
    assert "edges" in data
    service_names = [n["service"] for n in data["nodes"]]
    assert "web-gateway" in service_names
    assert "auth-service" in service_names
    assert "order-service" in service_names
    assert "inventory-service" in service_names
    assert "payment-service" in service_names

    # Check that configured edges exist
    edge_pairs = [(e["source"], e["target"]) for e in data["edges"]]
    assert ("web-gateway", "order-service") in edge_pairs
    assert ("order-service", "inventory-service") in edge_pairs

def test_radar_impact_analysis_failing_component():
    """Inject failure in inventory-service and verify graph traversal and impact ranking."""
    # 1. Trigger DB exhaustion scenario on inventory-service
    client.post("/api/demo/scenario/db_pool_exhaustion?count=3")

    # 2. Analyze impact of inventory-service
    res = client.post(
        "/api/radar/analyze",
        json={"suspected_component": "inventory-service", "window_seconds": 300}
    )
    assert res.status_code == 200
    report = res.json()

    assert report["suspected_component"] == "inventory-service"
    assert len(report["impacted_components"]) >= 3

    # Map by service name
    comp_map = {c["service"]: c for c in report["impacted_components"]}

    # Target suspect check (Priority 1)
    target = comp_map["inventory-service"]
    assert target["relationship"] == DependencyRelationship.TARGET.value
    assert target["priority"] == 1
    assert target["observed_failure"] is True
    assert target["status"] == ComponentHealthStatus.FAILING.value

    # Direct caller check (order-service)
    order_svc = comp_map["order-service"]
    assert order_svc["relationship"] == DependencyRelationship.DIRECT_DEPENDENT.value
    assert order_svc["distance"] == 1
    assert order_svc["observed_failure"] is True
    assert order_svc["status"] == ComponentHealthStatus.FAILING.value
    assert order_svc["priority"] == 2

    # Transitive caller check (web-gateway)
    gateway_svc = comp_map["web-gateway"]
    assert gateway_svc["relationship"] == DependencyRelationship.TRANSITIVE_DEPENDENT.value
    assert gateway_svc["distance"] == 2
    assert gateway_svc["observed_failure"] is True
    assert gateway_svc["status"] == ComponentHealthStatus.FAILING.value
    assert gateway_svc["priority"] == 3

    # Check dependency paths and evidence
    assert any("order-service" in p and "inventory-service" in p for p in report["dependency_paths"])
    assert len(report["supporting_evidence"]) > 0
    assert len(report["suggested_investigation_steps"]) > 0

def test_radar_impact_analysis_unfailing_component():
    """Verify that healthy callers are marked 'at_risk' rather than 'failing' when no errors exist."""
    # Run analysis without injecting failures
    res = client.post(
        "/api/radar/analyze",
        json={"suspected_component": "inventory-service", "window_seconds": 300}
    )
    assert res.status_code == 200
    report = res.json()

    comp_map = {c["service"]: c for c in report["impacted_components"]}
    order_svc = comp_map["order-service"]

    # Without errors in telemetry window, order-service is at_risk, not failing
    assert order_svc["observed_failure"] is False
    assert order_svc["status"] == ComponentHealthStatus.AT_RISK.value
    assert order_svc["priority"] == 4  # Lower priority than failing callers

# ==========================================
# Feature 5: Controlled Fix Validation Tests
# ==========================================

def test_validation_list_scenarios():
    """Verify available failure scenarios and their candidate fixes."""
    res = client.get("/api/validation/scenarios")
    assert res.status_code == 200
    scenarios = res.json()

    scenario_ids = [s["id"] for s in scenarios]
    assert "db_pool_exhaustion" in scenario_ids
    assert "bad_auth_deployment" in scenario_ids
    assert "payment_timeout" in scenario_ids

    # Check candidate fixes exist for db_pool_exhaustion
    db_scen = next(s for s in scenarios if s["id"] == "db_pool_exhaustion")
    fix_ids = [f["id"] for f in db_scen["available_fixes"]]
    assert "increase_pool_size" in fix_ids
    assert "noop_ineffective_fix" in fix_ids

def test_validation_baseline_and_successful_fix():
    """Scenario 1: Run baseline on db_pool_exhaustion and validate with increase_pool_size fix."""
    # 1. Run baseline experiment
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 5}
    )
    assert base_res.status_code == 200
    baseline = base_res.json()

    assert baseline["scenario_id"] == "db_pool_exhaustion"
    assert baseline["metrics"]["total_requests"] == 5
    assert baseline["metrics"]["failed_requests"] == 5
    assert baseline["metrics"]["error_rate"] == 1.0
    assert baseline["metrics"]["latency_p95_ms"] is not None
    exp_id = baseline["experiment_id"]

    # 2. Run fix validation with user approval
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
    val_report = val_res.json()

    assert val_report["experiment_id"] == exp_id
    assert val_report["verdict"] == ValidationVerdict.SUPPORTED_BY_EVIDENCE.value
    assert val_report["post_fix_metrics"]["failed_requests"] == 0
    assert val_report["post_fix_metrics"]["error_rate"] == 0.0
    assert val_report["error_rate_delta"] == 1.0
    assert "supported by telemetry evidence" in val_report["explanation"]

def test_validation_bad_auth_deployment_and_rollback():
    """Scenario 2: Run baseline on bad_auth_deployment and validate rollback fix."""
    # 1. Baseline
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "bad_auth_deployment", "workload_count": 4}
    )
    assert base_res.status_code == 200
    exp_id = base_res.json()["experiment_id"]
    assert base_res.json()["metrics"]["error_rate"] == 1.0

    # 2. Validation with rollback
    val_res = client.post(
        "/api/validation/run",
        json={
            "experiment_id": exp_id,
            "fix_id": "rollback_deployment",
            "approved": True,
            "workload_count": 4
        }
    )
    assert val_res.status_code == 200
    val_report = val_res.json()

    assert val_report["verdict"] == ValidationVerdict.SUPPORTED_BY_EVIDENCE.value
    assert val_report["post_fix_metrics"]["error_rate"] == 0.0

def test_validation_ineffective_fix_fails():
    """Test that applying an ineffective candidate fix returns not_supported_by_evidence."""
    # 1. Baseline
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 4}
    )
    exp_id = base_res.json()["experiment_id"]

    # 2. Apply ineffective fix
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
    val_report = val_res.json()

    assert val_report["verdict"] == ValidationVerdict.NOT_SUPPORTED_BY_EVIDENCE.value
    assert val_report["post_fix_metrics"]["error_rate"] >= 0.5
    assert "NOT supported by evidence" in val_report["explanation"]

def test_validation_inconclusive_due_to_small_sample():
    """Test that a tiny sample size (< 3 requests) produces an inconclusive verdict."""
    # 1. Baseline with 1 request
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 1}
    )
    exp_id = base_res.json()["experiment_id"]

    # 2. Validate with 1 request
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
    val_report = val_res.json()

    assert val_report["verdict"] == ValidationVerdict.INCONCLUSIVE.value
    assert "sample size" in val_report["explanation"].lower()

def test_validation_requires_explicit_user_approval():
    """Safety test: Attempting to apply a fix without approved=True must return 400 Bad Request."""
    base_res = client.post(
        "/api/validation/baseline",
        json={"scenario_id": "db_pool_exhaustion", "workload_count": 3}
    )
    exp_id = base_res.json()["experiment_id"]

    val_res = client.post(
        "/api/validation/run",
        json={
            "experiment_id": exp_id,
            "fix_id": "increase_pool_size",
            "approved": False,
            "workload_count": 3
        }
    )
    assert val_res.status_code == 400
    assert "approval is mandatory" in val_res.json()["detail"].lower()
